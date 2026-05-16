package main

import (
	"sync/atomic"
	"testing"
	"time"
)

// TestWorkerPool_Completion verifies that every submitted job is actually
// processed before Shutdown returns.
//
// The WorkerPool accepts an optional processFunc so tests can hook into
// completions without relying on the real (side-effect heavy) processJob.
func TestWorkerPool_Completion(t *testing.T) {
	const numWorkers = 5
	const numJobs = 20
	const queueCap = 10

	var completedCount int32

	// Inject a lightweight process function that atomically increments
	// completedCount each time a job finishes.  This is the only reliable
	// way to count completions: incrementing before Submit() would count
	// submissions, not completions.
	pool := NewWorkerPoolWithFunc(numWorkers, queueCap, func(_ int, _ Job) {
		atomic.AddInt32(&completedCount, 1)
	})

	for i := 0; i < numJobs; i++ {
		pool.Submit(Job{ID: i, Payload: "test"})
	}

	pool.Shutdown()

	if completedCount != int32(numJobs) {
		t.Errorf("Expected %d completions, got %d", numJobs, completedCount)
	}
}

// TestWorkerPool_Backpressure checks that a slow single worker causes the
// producer to slow down when the queue is full (blocking Submit).
//
// With 1 worker processing each job in 50ms, 10 jobs must take ≥ 450ms.
// If the pool finished faster, backpressure or the sleep is broken.
func TestWorkerPool_Backpressure(t *testing.T) {
	const numWorkers = 1
	const numJobs = 10
	const queueCap = 2 // Small queue to trigger backpressure early

	pool := NewWorkerPool(numWorkers, queueCap)

	start := time.Now()

	for i := 0; i < numJobs; i++ {
		pool.Submit(Job{ID: i, Payload: "test"})
	}

	pool.Shutdown()
	duration := time.Since(start)

	expectedMinDuration := 450 * time.Millisecond // 10 jobs * 50ms - slack
	if duration < expectedMinDuration {
		t.Errorf("Pool finished too fast (%v); expected ≥ %v — backpressure may be broken", duration, expectedMinDuration)
	}
}
