package main

import (
	"fmt"
	"hash/fnv"
	"sort"
	"strconv"
)

type ringEntry struct {
	hash uint32
	node string
}

type ConsistentHashRing struct {
	entries          []ringEntry
	virtualReplicas  int
	uniqueNodeLookup map[string]bool
}

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

func hashValue(input string) uint32 {
	h := fnv.New32a()
	_, _ = h.Write([]byte(input))
	return h.Sum32()
}

func (r *ConsistentHashRing) AddNode(node string) {
	if r.uniqueNodeLookup[node] {
		return
	}

	r.uniqueNodeLookup[node] = true

	for i := 0; i < r.virtualReplicas; i++ {
		key := node + "#" + strconv.Itoa(i)
		r.entries = append(r.entries, ringEntry{hash: hashValue(key), node: node})
	}

	sort.Slice(r.entries, func(i, j int) bool {
		return r.entries[i].hash < r.entries[j].hash
	})
}

func (r *ConsistentHashRing) GetNode(key string) string {
	if len(r.entries) == 0 {
		panic("ring has no nodes")
	}

	target := hashValue(key)
	idx := sort.Search(len(r.entries), func(i int) bool {
		return r.entries[i].hash >= target
	})

	if idx == len(r.entries) {
		idx = 0
	}

	return r.entries[idx].node
}

func main() {
	ring := NewConsistentHashRing(50)
	ring.AddNode("cache-a")
	ring.AddNode("cache-b")
	ring.AddNode("cache-c")

	keys := []string{"user:1", "user:2", "user:3", "user:999", "cart:91", "cart:92"}

	fmt.Println("Initial mapping:")
	for _, key := range keys {
		fmt.Printf("%s -> %s\n", key, ring.GetNode(key))
	}

	ring.AddNode("cache-d")
	fmt.Println("\nAfter adding cache-d (limited remapping expected):")
	for _, key := range keys {
		fmt.Printf("%s -> %s\n", key, ring.GetNode(key))
	}
}
