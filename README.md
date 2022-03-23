# P2P-Asynchronous-File-Sharing-Application
![image](https://user-images.githubusercontent.com/71888304/159639840-da2492a8-64d1-4425-ba9f-3f350d862712.png)
![image](https://user-images.githubusercontent.com/71888304/159639897-a04001ae-463f-435b-b2eb-5c395bbf10a4.png)
![image](https://user-images.githubusercontent.com/71888304/159640000-3b7b75b9-1d40-48dd-8693-55c24cbb91e5.png)

The objective of the Project is to allow users to download media files such as music, pdf, and music using a P2P software client that searches for other connected computers, handled by one central server. Multiple clients, also called as peers, are computer systems that may join the file sharing system by connecting to the tracker and declaring the list of the files that wish to be shared. 

The tracker keeps a list of the files which are shared among the network. The files being distributed are divided into chunks and for each file, the tracker handles the list of chunks each peer has. Once a peer receives a new chunk of the file it becomes a source for that chunk to be shared among other peers. When a peer tries to download a file, it will initiate a direct connection to the peers which have the file (or chunks of it) to download the file and will be able to download different chunks of the file simultaneously from several peers. 
