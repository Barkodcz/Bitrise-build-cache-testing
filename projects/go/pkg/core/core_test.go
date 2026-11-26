package core

import "testing"

func TestGreeting(t *testing.T) {
	if Greeting() == "" {
		t.Fatal("Greeting() returned an empty string")
	}
}
