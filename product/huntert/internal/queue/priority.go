package queue

import (
	"container/heap"
	"sync"
)

type Candidate struct {
	Path   string   `json:"path"`
	Tokens []string `json:"tokens"`
	Score  float64  `json:"score"`
	Depth  int      `json:"depth"`
	Source string   `json:"source"`
	index  int
}

type priorityHeap []*Candidate

func (h priorityHeap) Len() int { return len(h) }

func (h priorityHeap) Less(i, j int) bool {
	if h[i].Score == h[j].Score {
		if h[i].Depth == h[j].Depth {
			return h[i].Path < h[j].Path
		}
		return h[i].Depth < h[j].Depth
	}
	return h[i].Score > h[j].Score
}

func (h priorityHeap) Swap(i, j int) {
	h[i], h[j] = h[j], h[i]
	h[i].index = i
	h[j].index = j
}

func (h *priorityHeap) Push(x any) {
	item := x.(*Candidate)
	item.index = len(*h)
	*h = append(*h, item)
}

func (h *priorityHeap) Pop() any {
	old := *h
	n := len(old)
	item := old[n-1]
	old[n-1] = nil
	item.index = -1
	*h = old[:n-1]
	return item
}

type PriorityQueue struct {
	mu     sync.Mutex
	cond   *sync.Cond
	items  priorityHeap
	closed bool
}

func New() *PriorityQueue {
	pq := &PriorityQueue{}
	pq.cond = sync.NewCond(&pq.mu)
	heap.Init(&pq.items)
	return pq
}

func (pq *PriorityQueue) Push(item *Candidate) bool {
	pq.mu.Lock()
	defer pq.mu.Unlock()
	if pq.closed {
		return false
	}
	heap.Push(&pq.items, item)
	pq.cond.Signal()
	return true
}

func (pq *PriorityQueue) Pop() (*Candidate, bool) {
	pq.mu.Lock()
	defer pq.mu.Unlock()
	for pq.items.Len() == 0 && !pq.closed {
		pq.cond.Wait()
	}
	if pq.items.Len() == 0 && pq.closed {
		return nil, false
	}
	item := heap.Pop(&pq.items).(*Candidate)
	return item, true
}

func (pq *PriorityQueue) Len() int {
	pq.mu.Lock()
	defer pq.mu.Unlock()
	return pq.items.Len()
}

func (pq *PriorityQueue) Stop() int {
	pq.mu.Lock()
	defer pq.mu.Unlock()
	dropped := pq.items.Len()
	pq.items = nil
	pq.closed = true
	pq.cond.Broadcast()
	return dropped
}

func (pq *PriorityQueue) Snapshot() []Candidate {
	pq.mu.Lock()
	defer pq.mu.Unlock()

	cloned := make(priorityHeap, len(pq.items))
	copy(cloned, pq.items)
	heap.Init(&cloned)

	items := make([]Candidate, 0, len(cloned))
	for cloned.Len() > 0 {
		item := heap.Pop(&cloned).(*Candidate)
		items = append(items, *item)
	}
	return items
}

func PushCandidate(pq *PriorityQueue, item *Candidate) bool {
	return pq.Push(item)
}

func PopCandidate(pq *PriorityQueue) *Candidate {
	item, ok := pq.Pop()
	if !ok {
		return nil
	}
	return item
}

func Snapshot(pq *PriorityQueue) []Candidate {
	return pq.Snapshot()
}
