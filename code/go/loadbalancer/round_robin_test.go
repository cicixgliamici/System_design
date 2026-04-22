package main

import (
	"sync"
	"testing"
)

func TestRoundRobin_Sequential(t *testing.T) {
	backends := []string{"api-1", "api-2", "api-3"}
	rr := NewRoundRobin(backends)

	expected := []string{"api-1", "api-2", "api-3", "api-1", "api-2", "api-3", "api-1"}

	for i, exp := range expected {
		got := rr.Next()
		if got != exp {
			t.Errorf("At step %d: expected %s, got %s", i, exp, got)
		}
	}
}

func TestRoundRobin_Concurrency(t *testing.T) {
	backends := []string{"api-1", "api-2", "api-3", "api-4"}
	rr := NewRoundRobin(backends)

	const numGoroutines = 100
	const requestsPerGoroutine = 100
	const totalRequests = numGoroutines * requestsPerGoroutine

	counts := make(map[string]int)
	var mu sync.Mutex
	var wg sync.WaitGroup

	wg.Add(numGoroutines)
	for i := 0; i < numGoroutines; i++ {
		go func() {
			defer wg.Done()
			for j := 0; j < requestsPerGoroutine; j++ {
				backend := rr.Next()
				mu.Lock()
				counts[backend]++
				mu.Unlock()
			}
		}()
	}

	wg.Wait()

	// In a perfect Round Robin with totalRequests being a multiple of len(backends),
	// each backend should have exactly totalRequests / len(backends)
	expectedCount := totalRequests / len(backends)

	for _, b := range backends {
		if counts[b] != expectedCount {
			t.Errorf("Backend %s received %d requests, expected %d", b, counts[b], expectedCount)
		}
	}
}

func TestRoundRobin_PanicOnEmpty(t *testing.T) {
	defer func() {
		if r := recover(); r == nil {
			t.Errorf("The code did not panic on empty backends")
		}
	}()

	NewRoundRobin([]string{})
}
