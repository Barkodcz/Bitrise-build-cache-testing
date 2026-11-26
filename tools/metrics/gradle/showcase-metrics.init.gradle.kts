// Gradle init script (spec §8.2): classifies every task's outcome (FROM-CACHE / EXECUTED /
// UP-TO-DATE / SKIPPED / NO-SOURCE) via the build-service + operation-completion-listener API,
// which is configuration-cache compatible (unlike the legacy TaskExecutionListener).
//
// Registered via `--init-script` by tools/run-gradle.sh. Writes
// $SHOWCASE_METRICS_DIR/.fragments/<scenario>__<phase>/gradle.json when the service is closed.
//
// IMPORTANT: the BuildService instance handed to BuildEventsListenerRegistry.onTaskCompletion() is
// an isolated instance, NOT the same object a later `provider.get()` (e.g. from `gradle.buildFinished`)
// returns — verified empirically (System.identityHashCode() differs between the two). So the report
// MUST be written from the service's own `close()` lifecycle method (which Gradle calls on the same
// instance that received the onFinish() events), not from a separately-fetched instance afterwards.
//
// Cross-check: tools/run-gradle.sh also tees `--console=plain` output and greps for `FROM-CACHE`
// as a second, independent signal (spec §8.2 "Gradle" row) — the two should roughly agree.

import org.gradle.tooling.events.FinishEvent
import org.gradle.tooling.events.OperationCompletionListener
import org.gradle.tooling.events.task.TaskFinishEvent
import org.gradle.tooling.events.task.TaskSuccessResult
import org.gradle.tooling.events.task.TaskSkippedResult
import org.gradle.api.internal.GradleInternal
import org.gradle.api.provider.Property
import org.gradle.api.services.BuildServiceParameters
import org.gradle.build.event.BuildEventsListenerRegistry
import java.io.File
import java.util.concurrent.ConcurrentHashMap

abstract class ShowcaseTaskOutcomeService :
    org.gradle.api.services.BuildService<ShowcaseTaskOutcomeService.Params>,
    OperationCompletionListener, AutoCloseable {

    interface Params : BuildServiceParameters {
        val outFile: Property<File>
    }

    private val executed = ConcurrentHashMap.newKeySet<String>()
    private val fromCache = ConcurrentHashMap.newKeySet<String>()
    private val upToDate = ConcurrentHashMap.newKeySet<String>()
    private val skipped = ConcurrentHashMap.newKeySet<String>()
    private val noSource = ConcurrentHashMap.newKeySet<String>()
    private val executedDurations = ConcurrentHashMap<String, Long>()

    override fun onFinish(event: FinishEvent) {
        if (event !is TaskFinishEvent) return
        val path = event.descriptor.taskPath
        when (val result = event.result) {
            is TaskSuccessResult -> {
                when {
                    result.isFromCache -> fromCache.add(path)
                    result.isUpToDate -> upToDate.add(path)
                    else -> {
                        executed.add(path)
                        executedDurations[path] = result.endTime - result.startTime
                    }
                }
            }
            is TaskSkippedResult -> {
                if (result.skipMessage == "NO-SOURCE") noSource.add(path) else skipped.add(path)
            }
            else -> { /* failed tasks: leave uncategorised, build-level failure is reported elsewhere */ }
        }
    }

    // Called by Gradle at the very end of the build, on this SAME instance — see note above.
    override fun close() {
        val outFile = parameters.outFile.get()
        val topExecuted = executedDurations.entries
            .sortedByDescending { it.value }
            .take(10)
            .map { """{"path":"${it.key}","duration_s":${it.value / 1000.0}}""" }
            .joinToString(",")
        val total = executed.size + fromCache.size + upToDate.size + skipped.size + noSource.size
        val fromCacheShare = if ((executed.size + fromCache.size) > 0)
            fromCache.size.toDouble() / (executed.size + fromCache.size) else 0.0
        outFile.parentFile.mkdirs()
        outFile.writeText(
            """
            {
              "tasks_total": $total,
              "executed": ${executed.size},
              "from_cache": ${fromCache.size},
              "up_to_date": ${upToDate.size},
              "skipped": ${skipped.size},
              "no_source": ${noSource.size},
              "from_cache_share": $fromCacheShare,
              "top_executed_tasks": [$topExecuted]
            }
            """.trimIndent()
        )
    }
}

val showcaseScenarioId = System.getenv("SHOWCASE_SCENARIO_ID") ?: "unknown"
val showcasePhase = System.getenv("SHOWCASE_PHASE") ?: "unknown"
val showcaseMetricsDir = System.getenv("SHOWCASE_METRICS_DIR")

if (showcaseMetricsDir != null) {
    val outFile = File(showcaseMetricsDir, ".fragments/${showcaseScenarioId}__${showcasePhase}/gradle.json")

    // BuildEventsListenerRegistry must come from Gradle's own (build-scoped) service registry, not a
    // Project's — a project-scoped lookup only ever sees that one project's task events.
    val serviceProvider = gradle.sharedServices.registerIfAbsent(
        "showcaseTaskOutcomeService", ShowcaseTaskOutcomeService::class.java
    ) {
        parameters.outFile.set(outFile)
    }
    val listenerRegistry = (gradle as GradleInternal).services.get(BuildEventsListenerRegistry::class.java)
    listenerRegistry.onTaskCompletion(serviceProvider)
}
