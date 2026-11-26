# A "widely depended" core module (spec §4.1) -- uses nokogiri (a real native-extension
# dependency) so bundle install has real, measurable, platform-specific content worth caching.
require "nokogiri"

module Core
  def self.greeting
    doc = Nokogiri::XML("<message>hello from showcase-core</message>")
    doc.at("message").text
  end
end
