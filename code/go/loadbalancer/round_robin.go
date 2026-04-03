package main

import (
	"fmt"
	"sync"
)

type RoundRobin struct {
	mu       sync.Mutex
	backends []string
	index    int
}

func NewRoundRobin(backends []string) *RoundRobin {
	if len(backends) == 0 {
		panic("backends must not be empty")
	}

	return &RoundRobin{
		backends: backends,
		index:    0,
	}
}

func (rr *RoundRobin) Next() string {
	rr.mu.Lock()
	defer rr.mu.Unlock()

	backend := rr.backends[rr.index]
	rr.index = (rr.index + 1) % len(rr.backends)
	return backend
}

func main() {
	rr := NewRoundRobin([]string{
		"api-1",
		"api-2",
		"api-3",
	})

	for i := 0; i < 10; i++ {
		fmt.Printf("request=%02d -> backend=%s\n", i, rr.Next())
	}
}

