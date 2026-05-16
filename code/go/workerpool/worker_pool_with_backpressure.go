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

// ProcessFunc is a function that processes a single job.
// Accepting it as a parameter makes the pool testable without side effects.
type ProcessFunc func(workerID int, job Job)

// WorkerPool manages a set of workers processing jobs from a channel.
type WorkerPool struct {
	workerCount int
	jobs        chan Job
	wg          sync.WaitGroup
	processFunc ProcessFunc
}

// defaultProcessFunc is the real work function used in production/demo mode.
// It prints progress and sleeps to simulate variable work cost.
func defaultProcessFunc(workerID int, job Job) {
	fmt.Printf("worker=%d processing job=%d payload=%s\n", workerID, job.ID, job.Payload)
	time.Sleep(50 * time.Millisecond)
}

// NewWorkerPool creates and starts a worker pool with the default process function.
func NewWorkerPool(workerCount int, queueCapacity int) *WorkerPool {
	return NewWorkerPoolWithFunc(workerCount, queueCapacity, defaultProcessFunc)
}

// NewWorkerPoolWithFunc creates and starts a worker pool with a custom process function.
// This variant is useful in tests where the caller needs to observe completions
// without the side effects (I/O, sleep) of the default implementation.
func NewWorkerPoolWithFunc(workerCount int, queueCapacity int, fn ProcessFunc) *WorkerPool {
	wp := &WorkerPool{
		workerCount: workerCount,
		jobs:        make(chan Job, queueCapacity),
		processFunc: fn,
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
				wp.processFunc(workerID, job)
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
