package main

import (
	"fmt"
	"sync"
)

// RoundRobin is a very simple load balancer.
//
// It keeps:
// - a list of backend servers
// - the index of the next backend to use
// - a mutex to make selection safe when multiple goroutines call Next()
//   at the same time
//
// The algorithm is cyclic:
// api-1 -> api-2 -> api-3 -> api-1 -> ...
type RoundRobin struct {
	mu       sync.Mutex
	backends []string
	index    int
}

// NewRoundRobin creates a new round-robin balancer.
//
// The backend list must not be empty, otherwise there would be no server
// available to handle requests.
func NewRoundRobin(backends []string) *RoundRobin {
	if len(backends) == 0 {
		panic("backends must not be empty")
	}

	return &RoundRobin{
		backends: backends,
		index:    0,
	}
}

// Next returns the backend that should receive the next request.
//
// Steps:
// 1. lock the mutex so no other goroutine can modify index at the same time
// 2. read the backend at the current index
// 3. advance the index
// 4. wrap around to the beginning when the end is reached
// 5. return the selected backend
func (rr *RoundRobin) Next() string {
	rr.mu.Lock()
	defer rr.mu.Unlock()

	// Pick the backend currently pointed to by index.
	backend := rr.backends[rr.index]

	// Move to the next backend.
	// The modulo makes the sequence circular:
	// 0 -> 1 -> 2 -> 0 -> 1 -> 2 -> ...
	rr.index = (rr.index + 1) % len(rr.backends)

	return backend
}

func main() {
	// Create a round-robin balancer with three backend servers.
	rr := NewRoundRobin([]string{
		"api-1",
		"api-2",
		"api-3",
	})

	// Simulate 10 incoming requests.
	// Each request is assigned to the next backend in cyclic order.
	for i := 0; i < 10; i++ {
		fmt.Printf("request=%02d -> backend=%s\n", i, rr.Next())
	}
}
