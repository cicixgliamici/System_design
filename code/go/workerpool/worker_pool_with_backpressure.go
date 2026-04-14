package main

import (
	"fmt"
	"sync"
	"time"
)

// Job represents a unit of work processed by workers.
type Job struct {
	ID      int
	Payload string
}

// processJob simulates business logic execution.
func processJob(workerID int, job Job) {
	// Print who is handling the job (educational visibility).
	fmt.Printf("worker=%d processing job=%d payload=%s\n", workerID, job.ID, job.Payload)

	// Simulate variable work cost.
	time.Sleep(120 * time.Millisecond)
}

func main() {
	// Configuration values kept explicit for learning purposes.
	const workerCount = 3
	const queueCapacity = 5
	const totalJobs = 12

	// Buffered channel acts as an in-memory queue.
	// Bounded capacity demonstrates simple backpressure.
	jobs := make(chan Job, queueCapacity)

	// WaitGroup lets main wait for all worker goroutines to stop cleanly.
	var wg sync.WaitGroup

	// Start worker goroutines.
	for workerID := 1; workerID <= workerCount; workerID++ {
		wg.Add(1)

		go func(id int) {
			defer wg.Done()

			// Range loop exits automatically when channel is closed.
			for job := range jobs {
				processJob(id, job)
			}

			fmt.Printf("worker=%d stopped\n", id)
		}(workerID)
	}

	// Producer loop: enqueue jobs.
	for i := 1; i <= totalJobs; i++ {
		job := Job{ID: i, Payload: fmt.Sprintf("task-%02d", i)}

		// If the queue is full, send blocks until workers consume items.
		// This is the simplest form of backpressure.
		jobs <- job
		fmt.Printf("enqueued job=%d queue_len=%d\n", job.ID, len(jobs))
	}

	// No more jobs: close channel so workers can finish.
	close(jobs)

	// Wait for all workers to complete.
	wg.Wait()

	fmt.Println("all jobs processed")
}
