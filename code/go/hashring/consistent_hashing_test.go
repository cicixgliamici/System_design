package main

import (
	"fmt"
	"testing"
)

func TestConsistentHashRing_BasicMapping(t *testing.T) {
	ring := NewConsistentHashRing(100)
	ring.AddNode("node1")
	ring.AddNode("node2")
	ring.AddNode("node3")

	// Ensure keys are consistently mapped to the same nodes
	key := "my-very-important-key"
	nodeA := ring.GetNode(key)
	nodeB := ring.GetNode(key)

	if nodeA != nodeB {
		t.Errorf("Inconsistent mapping: key %s mapped to %s and then %s", key, nodeA, nodeB)
	}

	if nodeA == "" {
		t.Error("Mapped node should not be empty")
	}
}

func TestConsistentHashRing_AddNodeMinimalRemapping(t *testing.T) {
	ring := NewConsistentHashRing(100)
	nodes := []string{"node1", "node2", "node3"}
	for _, n := range nodes {
		ring.AddNode(n)
	}

	// Map 1000 keys
	numKeys := 1000
	initialMapping := make(map[int]string)
	for i := 0; i < numKeys; i++ {
		key := fmt.Sprintf("key-%d", i)
		initialMapping[i] = ring.GetNode(key)
	}

	// Add a new node
	ring.AddNode("node4")

	// Check how many keys moved
	movedKeys := 0
	for i := 0; i < numKeys; i++ {
		key := fmt.Sprintf("key-%d", i)
		newNode := ring.GetNode(key)
		if newNode != initialMapping[i] {
			movedKeys++
			// In consistent hashing, keys should only move TO the new node
			if newNode != "node4" {
				t.Errorf("Key %d moved from %s to %s, but should only move to node4", i, initialMapping[i], newNode)
			}
		}
	}

	// Statistical check: roughly 1/4 of keys should move to node4 (since we now have 4 nodes)
	// We allow some margin (e.g., between 15% and 35%)
	percentageMoved := float64(movedKeys) / float64(numKeys) * 100
	fmt.Printf("Keys moved after adding node4: %d (%.2f%%)\n", movedKeys, percentageMoved)

	if percentageMoved < 15 || percentageMoved > 35 {
		t.Errorf("Unexpected remapping percentage: %.2f%%. Expected around 25%%.", percentageMoved)
	}
}

func TestConsistentHashRing_VirtualReplicasDistribution(t *testing.T) {
	// With 1 replica, distribution might be very uneven.
	// With 200 replicas, it should be much more balanced.
	numKeys := 10000
	nodes := []string{"node1", "node2", "node3", "node4"}

	runDistributionTest := func(replicas int) map[string]int {
		ring := NewConsistentHashRing(replicas)
		for _, n := range nodes {
			ring.AddNode(n)
		}

		distribution := make(map[string]int)
		for i := 0; i < numKeys; i++ {
			node := ring.GetNode(fmt.Sprintf("key-%d", i))
			distribution[node]++
		}
		return distribution
	}

	distLow := runDistributionTest(1)
	distHigh := runDistributionTest(200)

	calcStdDev := func(dist map[string]int) float64 {
		mean := float64(numKeys) / float64(len(nodes))
		var sumSquares float64
		for _, count := range dist {
			diff := float64(count) - mean
			sumSquares += diff * diff
		}
		return sumSquares / float64(len(nodes))
	}

	stdDevLow := calcStdDev(distLow)
	stdDevHigh := calcStdDev(distHigh)

	fmt.Printf("StdDev with 1 replica: %.2f\n", stdDevLow)
	fmt.Printf("StdDev with 200 replicas: %.2f\n", stdDevHigh)

	if stdDevHigh >= stdDevLow {
		t.Errorf("Virtual replicas did not improve distribution. Low: %.2f, High: %.2f", stdDevLow, stdDevHigh)
	}
}
