package main

import (
	"fmt"
	"hash/fnv"
	"sort"
	"strconv"
)

// ringEntry represents one point on the hash ring.
// Each physical node is represented multiple times through virtual replicas,
// so the same node can appear in many ringEntry values with different hashes.
type ringEntry struct {
	hash uint32
	node string
}

// ConsistentHashRing models a hash ring used to distribute keys across nodes.
//
// Main ideas:
// - entries: all virtual nodes placed on the ring, sorted by hash value
// - virtualReplicas: number of virtual nodes for each physical node
// - uniqueNodeLookup: prevents adding the same physical node more than once
type ConsistentHashRing struct {
	entries          []ringEntry
	virtualReplicas  int
	uniqueNodeLookup map[string]bool
}

// NewConsistentHashRing creates a new ring.
// virtualReplicas must be > 0, otherwise the distribution would not work.
func NewConsistentHashRing(virtualReplicas int) *ConsistentHashRing {
	if virtualReplicas <= 0 {
		panic("virtualReplicas must be > 0")
	}

	return &ConsistentHashRing{
		entries:          make([]ringEntry, 0),
		virtualReplicas:  virtualReplicas,
		uniqueNodeLookup: make(map[string]bool),
	}
}

// hashValue computes a deterministic 32-bit hash for a string.
// FNV-1a is simple and fast, making it suitable for a demo/example like this.
func hashValue(input string) uint32 {
	h := fnv.New32a()
	_, _ = h.Write([]byte(input))
	return h.Sum32()
}

// AddNode inserts a new physical node into the ring.
//
// Instead of placing the node only once, we create many virtual replicas
// (for example cache-a#0, cache-a#1, ..., cache-a#49).
// This helps achieve a more even key distribution across nodes.
func (r *ConsistentHashRing) AddNode(node string) {
	// Do nothing if the node is already present.
	if r.uniqueNodeLookup[node] {
		return
	}

	r.uniqueNodeLookup[node] = true

	// Create virtual replicas for the node.
	for i := 0; i < r.virtualReplicas; i++ {
		key := node + "#" + strconv.Itoa(i)
		r.entries = append(r.entries, ringEntry{
			hash: hashValue(key),
			node: node,
		})
	}

	// Keep the ring sorted by hash so we can use binary search in GetNode.
	sort.Slice(r.entries, func(i, j int) bool {
		return r.entries[i].hash < r.entries[j].hash
	})
}

// GetNode returns the node responsible for the given key.
//
// Algorithm:
// 1. Hash the key.
// 2. Find the first ring entry whose hash is >= key hash.
// 3. If none exists, wrap around to the first entry in the ring.
//
// This "wrap-around" behavior is what makes the structure a ring.
func (r *ConsistentHashRing) GetNode(key string) string {
	if len(r.entries) == 0 {
		panic("ring has no nodes")
	}

	target := hashValue(key)

	// Binary search over the sorted ring.
	idx := sort.Search(len(r.entries), func(i int) bool {
		return r.entries[i].hash >= target
	})

	// If we went past the end, wrap around to the beginning.
	if idx == len(r.entries) {
		idx = 0
	}

	return r.entries[idx].node
}

func main() {
	// Create a ring with 50 virtual replicas per node.
	ring := NewConsistentHashRing(50)

	// Add three cache nodes.
	ring.AddNode("cache-a")
	ring.AddNode("cache-b")
	ring.AddNode("cache-c")

	keys := []string{"user:1", "user:2", "user:3", "user:999", "cart:91", "cart:92"}

	fmt.Println("Initial mapping:")
	for _, key := range keys {
		fmt.Printf("%s -> %s\n", key, ring.GetNode(key))
	}

	// Add a new node.
	// In consistent hashing, only part of the keys should move to the new node,
	// not all of them as would happen in many naive modulo-based strategies.
	ring.AddNode("cache-d")

	fmt.Println("\nAfter adding cache-d (limited remapping expected):")
	for _, key := range keys {
		fmt.Printf("%s -> %s\n", key, ring.GetNode(key))
	}
}
