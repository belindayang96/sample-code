## UCSC CSPS 128 Distributed System course project
Some guidelines given:


In the previous assignment, you implemented a distributed system that extended a single-site key-value store with replication in order to make it tolerant to faults such as node crashes and network partitions.  To put it another way, we added more computers to make the system more resilient. Distributed systems may be hard to program, but it can be worth it!

Resilience is not the only reason, however, to take on the complexity of distributed programming.  By adding more processing power to our system in the form of additional nodes, we can sometimes perform the same amount of work faster (this is sometimes called speedup), or gain the ability to do more work (this sometimes called scaleup or scaleout) than a single machine could do, by dividing the work across machines in an intelligent way.

The trick that will allow our storage systems to achieve speedup and/or scaleout is dividing the data in such a way that each data item belongs in a single shard (sometimes called a partition, but we will try to avoid that overloaded term) or replica group.  That way, as we add more shards to the system we increase its capacity, allowing it to store more data and perform more independent, parallel work.

Note that sharding is completely orthogonal to replication; we can add shards to the system and we can add replicas to a shard; the latter increases our fault tolerance and the former (in general) increases our performance by increasing our capacity.

In order to implement a sharded KVS you will need to choose a strategy for deciding which shard each data item belong on.  A good sharding policy will distribute the data more or less uniformly among the nodes (can you see why?)  As shards are added and removed from the system via view change operations, the data items will need to be redistributed in order to maintain a uniform distribution.
