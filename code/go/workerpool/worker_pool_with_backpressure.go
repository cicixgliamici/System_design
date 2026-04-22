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

// WorkerPool manages a set of workers processing jobs from a channel.
type WorkerPool struct {
	workerCount int
	jobs        chan Job
	wg          sync.WaitGroup
}

// NewWorkerPool creates and starts a worker pool.
func NewWorkerPool(workerCount int, queueCapacity int) *WorkerPool {
	wp := &WorkerPool{
		workerCount: workerCount,
		jobs:        make(chan Job, queueCapacity),
	}

	wp.start()
	return wp
}

func (wp *WorkerPool) start() {
	for i := 1; i <= wp.workerCount; i++ {
		wp.wg.Add(1)
		go func(workerID int) {
			defer wp.wg.Done()
			for job := range wp.jobs {
				wp.processJob(workerID, job)
			}
		}(i)
	}
}

// Submit adds a job to the pool. It blocks if the queue is full (backpressure).
func (wp *WorkerPool) Submit(job Job) {
	wp.jobs <- job
}

// Shutdown closes the job channel and waits for all workers to finish.
func (wp *WorkerPool) Shutdown() {
	close(wp.jobs)
	wp.wg.Wait()
}

func (wp *WorkerPool) processJob(workerID int, job Job) {
	// Print who is handling the job (educational visibility).
	fmt.Printf("worker=%d processing job=%d payload=%s\n", workerID, job.ID, job.Payload)

	// Simulate variable work cost.
	time.Sleep(50 * time.Millisecond)
}

func main() {
	const workerCount = 3
	const queueCapacity = 5
	const totalJobs = 12

	pool := NewWorkerPool(workerCount, queueCapacity)

	// Producer loop: enqueue jobs.
	for i := 1; i <= totalJobs; i++ {
		job := Job{ID: i, Payload: fmt.Sprintf("task-%02d", i)}
		pool.Submit(job)
		fmt.Printf("enqueued job=%d\n", job.ID)
	}

	pool.Shutdown()
	fmt.Println("all jobs processed")
}
