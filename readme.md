a. File structure: I used JSON files for saving data and for each user we have a separate file. I used this structure because it is much easier to make them parallel and using 
  a separate lock for each file.
b. Synchronization mechanisms: Each thread has a separate lock. Locks are held in an global key-value array so each user for each thread can access it with its username.
  Using their locks for critical sections makes the program safe and avoids race conditions.
c. DeadLock avoidness: I use the usernames for preventing DeadLocks. when I want to lock to dependent threads I compare their usernames alphabetically and the smaller string
  will be locked first. So the program never goes in DeadLock. I used this approach because it is easy and also never goes in deadlock.
d. Transaction management: For having atomic transactions I temp the data of Users before making any change on them. If the transaction raises an exeption, the temporary data will 
  be saved again in JSON files, so the system status is in last safe state.
e. Challenges and solutions: For handling DeadLocks I had some challenges and I realized this can be the best approach for this program. Also I hade some challenges with reading
  JSON files in python because sometimes it raises exception for reading them and so the transactions will not be completed.
