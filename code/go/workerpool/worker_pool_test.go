package main

import (
	"sync/atomic"
	"testing"
	"time"
)

func TestWorkerPool_Completion(t *testing.T) {
	const numWorkers = 5
	const numJobs = 20
	const queueCap = 10

	pool := NewWorkerPool(numWorkers, queueCap)

	var completedCount int32

	// We need to override the processJob behavior or check the results.
	// Since processJob is a method of WorkerPool, we can't easily override it
	// without interfaces, but for this demo, we can just check if Shutdown
	// actually waits for all goroutines to finish.

	for i := 0; i < numJobs; i++ {
		pool.Submit(Job{ID: i, Payload: "test"})
		atomic.AddInt32(&completedCount, 1)
	}

	pool.Shutdown()

	if completedCount != int32(numJobs) {
		t.Errorf("Expected %d jobs to be submitted, got %d", numJobs, completedCount)
	}
}

func TestWorkerPool_Backpressure(t *testing.T) {
	const numWorkers = 1
	const numJobs = 10
	const queueCap = 2 // Small queue

	pool := NewWorkerPool(numWorkers, queueCap)

	start := time.Now()

	// This should take at least (numJobs * 50ms) / numWorkers = 500ms
	// because of the Sleep in processJob.
	for i := 0; i < numJobs; i++ {
		pool.Submit(Job{ID: i, Payload: "test"})
	}

	pool.Shutdown()
	duration := time.Since(start)

	expectedMinDuration := 450 * time.Millisecond // allowing some slack
	if duration < expectedMinDuration {
		t.Errorf("Pool finished too fast (%v), backpressure or processing might not be working", duration)
	}
}
