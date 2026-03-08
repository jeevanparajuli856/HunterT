PDF Download

3689932.3694770.pdf

07 March 2026

Total Citations: 4

. 

Total Downloads: 847

. 

Latest updates: hps://dl.acm.org/doi/10.1145/3689932.3694770

. 

. 

Published: 22 November 2024

. 

. 

. 

RESEARCH-ARTICLE

. 

Citation in BibTeX format

Offensive AI: Enhancing Directory Brute-forcing Aack with the Use of

. 

. 

Language Models

CCS '24: ACM SIGSAC Conference on

Computer and Communications Security

*October 14 - 18, 2024*

ALBERTO CASTAGNARO, Del University of Technology, Del, Zuid-Holland, Netherlands

*UT, Salt Lake City, USA*

. 

. 

. 

MAURO CONTI, University of Padua, Padua, PD, Italy

Conference Sponsors:

SIGSAC

. 

LUCA PAJOLA, University of Padua, Padua, PD, Italy

. 

. 

. Open Access Support provided by:

. University of Padua

. Del University of Technology

. 

AISec '24: Proceedings of the 2024 Workshop on Artificial Intelligence and Security \(November 2024\) hps://doi.org/10.1145/3689932.3694770

ISBN: 9798400712289

. 



Offensive AI: Enhancing Directory Brute-forcing Attack with the Use of Language Models

∗ †

†

Alberto Castagnaro

Mauro Conti

Luca Pajola

Delft University of Technology

University of Padua

University of Padua

Delft, The Netherlands

Padua, Italy

Padua, Italy

A.Castagnaro@student.tudelft.nl

mauro.conti@unipd.it

luca.pajola@unipd.it

Abstract

fixed before malicious actors exploit them. Directory enumeration is a critical component of security assessments. It involves identify-Web Vulnerability Assessment and Penetration Testing \(Web VAPT\) ing accessible directories, files, and web paths in a web application. 

is a comprehensive cybersecurity process that uncovers a range of Effective discovery attacks, such as directory brute-forcing, can vulnerabilities which, if exploited, could compromise the integrity uncover hidden directories and files that may contain sensitive data of web applications. In a VAPT, it is common to perform a Directory brute-forcing Attack

or critical functionalities. 

, aiming at the identification of accessible

Offensive AI uses artificial intelligence technologies to conduct directories of a target website. Current commercial solutions are or enhance cyber attacks \[10, 13\]. This emerging field combines AI’s inefficient as they are based on brute-forcing strategies that use adaptability and learning capabilities with traditional attack vectors, wordlists, resulting in enormous quantities of trials for a small creating more sophisticated and automated threats. Offensive AI can amount of success. 

rapidly analyze vast amounts of data, adapt to defensive measures, Offensive AI is a recent paradigm that integrates AI-based tech-and execute attacks with increased speed and complexity. 

nologies in cyber attacks. In this work, we explore whether AI can enhance the directory enumeration process and propose a novel Contribution. This paper contributes to the field by presenting a Language Model-based framework. Our experiments – conducted novel approach that leverages Language Models \(LMs\) to enhance in a testbed consisting of 1 million URLs from different web appli-the efficiency and effectiveness of directory brute-forcing attacks. 

cation domains \(universities, hospitals, government, companies\) –

Our method builds on prior knowledge retrieved by different web demonstrate the superiority of the LM-based attack, with an aver-applications and then exploits embeddings to extrapolate the con-age performance increase of 969%. 

text of different words that form web paths and language models to CCS Concepts

generate new possible URL \(Uniform Resource Locator\) paths that can be used to send requests. Our contributions are summarized

• Security and privacy → Penetration testing; • Computing below:

methodologies → Natural language generation. 

\(1\) We designed a novel dataset containing 4 distinct types of Keywords

applications that are often the targets for attacks, i.e., commercial, government, hospital, and universities, for a total Offensive AI, Language Model, Web Security, Penetration Test of 1 million of URLs. 

ACM Reference Format:

\(2\) We propose two novel directory brute-forcing attacks that Alberto Castagnaro, Mauro Conti, and Luca Pajola. 2024. Offensive AI: leverage prior knowledge: a probabilistic and a Language Enhancing Directory Brute-forcing Attack with the Use of Language Models. 

Model-based approach. 

In Proceedings of the 2024 Workshop on Artificial Intelligence and Security \(AISec ’24\), October 14–18, 2024, Salt Lake City, UT, USA. 

\(3\) A systematic evaluation highlights the superiority of prior ACM, New York, 

knowledge approaches compared to baselines. LM-based at-NY, USA, 12 pages. https://doi.org/10.1145/3689932.3694770

tacks outperform all 8 proposed baselines, with an average 1

Introduction

performance increase of 969%. On the other hand, probabilistic approaches show high performance when the budget In its most general sense, hacking refers to modifying or manipu-of spendable requests is limited and, therefore, optimal for lating a system’s features to achieve a goal outside of the creator’s stealthier attacks. 

original purpose. While often associated with illegal cyber activities, hacking can also be performed ethically, with permission, to We provide the code to replicate our experiments at: https://

improve system security and uncover vulnerabilities that can be

github.com/spritzmatterorg/LM- Directory- Bruteforcing. 

∗ Also with Delft University of Technology. 

Ethical Disclaimer. The techniques and methods discussed in

† Also with Spritz Matter Srl. 

this paper are intended for educational purposes and ethical security testing only. The authors do not condone the use of these

This work is licensed under a Creative Commons Attribution

International 4.0 License. 

methods for malicious purposes and strongly advocate for responsible disclosure and remediation of identified vulnerabilities. We AISec ’24, October 14–18, 2024, Salt Lake City, UT, USA hope that this research will contribute to the development of more

© 2024 Copyright held by the owner/author\(s\). 

secure web environments and the advancement of cybersecurity ACM ISBN 979-8-4007-1228-9/24/10

https://doi.org/10.1145/3689932.3694770

practices. For this reason, we do not share publicly the collected 184



AISec ’24, October 14–18, 2024, Salt Lake City, UT, USA Alberto Castagnaro, Mauro Conti, & Luca Pajola dataset and code. Researchers willing to reproduce our experiment 3

Threat model

are invited to contact the authors. 

Attack Description. A directory enumeration brute-force attack is a method that checks for and attempts to access directories and 2

Background

files on a web server that are not referenced by the application but This section describes the theory behind Language Models \[16–18\]. 

are still accessible. This type of attack is performed by generating a Language Models \(LMs\) are statistical models that learn the proba-large number of requests associated with different URLs sent to the bility distribution of sequences of words in a language. Their objec-server. The attack is commonly based on a wordlist, a list of words tive is to predict the likelihood of a word given the context of preced-used to construct the URLs starting from the base one the attacker \(1\)

\(𝑡 \)

ing words. Formally, given a sequence of words x = \(𝑥

, . . . , 𝑥

\), 

selects. 

\(𝑡 \+1\)

LMs computes the probability distribution of the next word 𝑥

:

The primary goal of a directory enumeration attack is to uncover \(

hidden files, directories, backup files, or administrative interfaces 𝑡 \+1\)

\(𝑡 \)

\(1\)

𝑃 \(𝑥

|𝑥

, . . . 𝑥

\), 

\(1\)

that may contain sensitive information or configuration data. If \(𝑡 \+1\)

where 𝑥

∈ 𝑉 = 𝑤1, . . . , 𝑤 |

these resources are not adequately secured, they can be exploited 𝑉 | , and 𝑉

is a fixed vocabulary. 

Given a sentence, the goal of a LM is to estimate the probability to gain unauthorized access, escalate privileges, or launch further of this sequence 𝑃 \(x\), which is obtained through the chain rule of attacks. Vulnerabilities typically exploited by such attacks include probability:

misconfigured permissions, default installations with sample files, \(1\)

\(

and outdated or unnecessary files left accessible on the server. 

𝑇 \)

\(1\)

\(2\)

\(1\)

𝑃 \( \(𝑥

, . . . , 𝑥

\)\) = 𝑃 \(𝑥

\) · 𝑝 \(𝑥

|𝑥

\) · . . . ·

Directory enumeration brute-force attacks are often employed \(𝑇 \)

\(𝑇 −1\)

\(1\)

𝑝 \(𝑥

|𝑥

, . . . , 𝑥

\)

during the reconnaissance phase of a penetration test. A penetration \(2\)

test, or pentest, is an authorized simulated cyberattack on a com-𝑇

Ö

=

\( \(𝑡 \)

\(𝑡 −1\)

\(1\)

𝑥

|𝑥

, . . . , 𝑥

\). 

puter system performed to evaluate its security. However, this type of attack may also be performed by malicious actors, so it is essen-𝑡 =1

tial to be aware of this type of attack and to test web application Modern LMs utilize neural networks to learn complex relation-security against it properly. 

ships between words and context. Recurrent Neural Networks \(RNN\) are ideal for the task, as they model the generative pro-Automated tools. Several commercial and open-source tools are cess of a sequence data \(e.g., time series, natural language\). Unlike commonly used to perform directory brute-force attacks. These other types of NN like feedforward NN, RNNs integrate feedback tools can be specific to this type of attack or be more broad-based connections that allow them to retain information from previous to provide other functionalities; additionally, they also often come time steps \(hidden state\), and then generate a new sample according with default wordlists. Popular tools are:

to a probability distribution given the hidden state. At each time 𝑡

𝑡

• Dirbuster, a Java-based, multi-threaded tool specifically de-step, a RNN computes an output 𝑦

based on the current input 𝑥

𝑡 −1

signed to brute force directories and file names on web and the hidden state ℎ

calculated at the previous step. 

1

or application servers developed by OWASP . It has nine \(𝑡 \)

\(𝑡 −1\)

\(𝑡 \)

ℎ

= 𝑓 \(ℎ

, 𝑥

\). 

\(3\)

different default wordlists. The tool is freely available at: LMs are trained on large text corpora, and their parameters are

www.kali.org/tools/dirbuster/. 

•

learned to maximize the likelihood of observed sequences \(max-Wfuzz, an open-source security tool designed to launch imum likelihood estimation\). The loss function at step brute-force attacks against web applications by fuzzing input 𝑡

is the

cross-entropy between predicted probability distribution ˆ

parameters and assisting penetration testers in identifying 𝑦

and

𝑡

the true next word

vulnerabilities. It is designed to perform several attacks, such 𝑦 :

𝑡

as brute-forcing, fuzzing, and injection attacks. It also comes \(

∑︁

𝑡 \)

\(𝑡 \)

\(𝑡 \)

\(𝑡 \)

𝐽

\(𝜃 \) = 𝐶𝐸 \(y\(𝑡 \), ˆy\(𝑡 \) \) = −

y

log ˆ

y

= − log ˆ

y

. 

𝑤

𝑤

x

with several wordlists covering a variety of contexts. The 𝑡 \+1

𝑤 ∈𝑉

tool is freely available at: wfuzz.readthedocs.io. 

\(4\)

• Burpsuite, a commercial platform that provides a graphical By averaging the previous on the entire training set, we obtain the tool for conducting security testing on online applications. It following overall loss:

supports the entire testing process, from initial mapping and 𝑇

𝑇

1 ∑︁

1 ∑︁

analysis of an application’s attack surface to the discovery 𝑡

\(𝑡 \)

𝐽 \(𝜃 \) =

𝐽

\(𝜃 \) =

− log ˆ

yx . 

\(5\)

𝑡 =1

and exploitation of security flaws. Among these, Burpsuite 𝑇

𝑇

𝑡 =1

𝑡 =1

can perform brute-force attacks to enumerate directories, Embedding representations play a crucial role in LMs. An em-given a target and a wordlist. The tool is available under bedding is a numerical representation of words, phrases, sentences, different licences at: portswigger.net/burp. 

or even entire documents. These representations are typically high-dimensional vectors that capture the semantic meaning of the text. 

Wordlists. Wordlists are essentially a set of directories utilized The importance of embeddings lies in their ability to transform in a brute-force attack. Therefore, they play a vital choice when text into a format that machine learning models can understand using these tools. A proper choice of wordlist can greatly impact and process. Therefore, embeddings capture the nuanced meanings the results, potentially uncovering more vulnerabilities. 

of words based on their context, which is essential for tasks like sentiment analysis, translation, and summarization. 

1 https://owasp.org/

185



Offensive AI: Enhancing Directory Brute-forcing Attack with the Use of Language Models AISec ’24, October 14–18, 2024, Salt Lake City, UT, USA In the context of directory brute-forcing attacks, there is a range For example, considering the paths "/news", "/home", "/register", of wordlist categories that fit different needs: from general-purpose

"/news/2024", "/news/today" and "/news/weather" as the paths wordlists to backup-file wordlists, CMS-specific \(Content manage-extracted from the crawl of a web application, we can visualize the ment system\) wordlists, and even more. 

corresponding reconstructed tree in Figure 1. 

Various automated tools are provided by default with various wordlists. However, many other user-created wordlists can be found on the Internet, and users may also create ad-hoc wordlists that satisfy their needs. In the scope of this research, we selected four general-purpose wordlists to assess:

• big\_wfuzz

2

\[BW\] : a Wfuzz default general-purpose wordlist that contains 3024 words. 

• top\_10k\_github

3

\[GH\] : a user-created wordlist in GitHub containing 10000 words, created selecting the most common words found in ten million URLs. 

• megabeast\_wfuzz

4

\[MW\] : another Wfuzz default general-purpose wordlist that contains 45459 words. 

• directory-list\_dirbuster

5

\[DB\] : a Dirbuster default wordlist containing 141835 words. 

Figure 1: Visualization of a reconstructed tree. 

4

Methodology

Overview. Traditional attacks are essentially inefficient, as they are based on brute-forcing mechanisms. In this work, we explore 4.1

Standard approach

two different approaches that might improve the attack: one based on probabilities and one using a Language Model for path gener-The standard wordlist-based approach that we will use to compare ation. Given the scope of this research, which aims to be general the results with our proposed approaches is based on two main and not to focus on specific technologies or sensitive information, strategies: Depth-First and Breadth-First. 

both approaches aim to highlight the feasibility of implementing Depth-First. In a directory brute-force attack, the Depth-First more efficient attacks and aim to exploit two features not used by approach prioritizes the exploration of subdirectories within a dis-the traditional wordlist-based brute-forcing approach: covered directory before moving on to other directories at the same

• Prior Knowledge. Web applications that belong to similar level. The algorithm initiates by sequentially sending HT TP re-categories might have a similar structure. Given a target quests using the entries in a wordlist. Upon receiving a positive website, using knowledge retrieved from similar websites response, which indicates the construction of a valid URL and, to decide what HT TP requests to send to the target website hence, the discovery of a valid directory, the algorithm shifts its may positively impact the results. 

focus to brute-forcing the subdirectories of this newly discovered

• Adaptive decision-making. During a directory brute-force directory. It exhaustively searches within these subdirectories be-attack, having the ability to dynamically decide which URLs fore it resumes brute-forcing other directories at the same depth to generate and which requests to send might improve the hit as the previously validated one. This approach ensures a compre-rate of successful responses and reduce ineffective requests. 

hensive search within each directory before moving on to the next, Tree reconstruction. 

thereby maximizing the chances of uncovering valuable informa-Before we discuss how traditional tools and

tion nested deep within the directory structure. An algorithmic rep-our proposed approaches work, it is helpful to understand how resentation of this approach can be visualized in Algorithm 1, where HT TP responses allow us to reconstruct the filesystem of a web constructURL\(URL, word\) is a function to generate a valid URL

application. Since a filesystem has a hierarchical tree structure, appending a word to the path of the URL and isValid\(response\) the paths of each web application can be used to reconstruct it. In is a function that checks if the response is valid. 

particular, we used the AnyTree class in Python to reconstruct the filesystems of each web application, considering as root the starting URL usually referred to as the target. This strategy allows us to Algorithm 1 Depth-First brute-force attack Pseudocode perform depth-level analysis and simulations of offline brute-force 1:

procedure DepthFirst\(𝑟𝑜𝑜𝑡𝑈 𝑅𝐿, 𝑤𝑜𝑟𝑑𝑙𝑖𝑠𝑡 \)

attacks so that we do not perform actual attacks on online web 2:

for each 𝑤𝑜𝑟𝑑 in 𝑤𝑜𝑟𝑑𝑙𝑖𝑠𝑡 do

applications, thus maintaining an ethical posture that still allows 3:

𝑢𝑟 𝑙 ← constructURL\(𝑟 𝑜𝑜𝑡𝑈 𝑅𝐿, 𝑤𝑜𝑟 𝑑 \)

4:

𝑟 𝑒𝑠 𝑝𝑜𝑛𝑠𝑒 ← sendHTTPrequest\(𝑢𝑟 𝑙 \)

us to obtain meaningful results. 

5:

if isValid\(𝑟𝑒𝑠𝑝𝑜𝑛𝑠𝑒\) then

6:

DepthFirst\(𝑢𝑟 𝑙 , 𝑤𝑜𝑟 𝑑𝑙 𝑖𝑠𝑡 \)

7:

end if

2 https://github.com/xmendez/wfuzz/blob/master/wordlist/general/big.txt

8:

end for

3 https://github.com/xajkep/wordlists/blob/master/discovery/top-10k-web-

9:

end procedure

directories\_from\_10M\_urlteam\_links.txt

4 https://github.com/xmendez/wfuzz/blob/master/wordlist/general/megabeast.txt

5 https://github.com/3ndG4me/KaliLists/blob/master/dirbuster/directory-list-1.0.txt

186



AISec ’24, October 14–18, 2024, Salt Lake City, UT, USA Alberto Castagnaro, Mauro Conti, & Luca Pajola Breadth-First. In contrast to the previous approach, the Breadth-

\(corresponding to a directory\), we would maintain a counter First approach prioritizes the exploration of directories at the same indicating how many times that particular node is repeated. 

level before delving into their subdirectories. The algorithm begins An example of this is reported in Figure 2. 

by sending HT TP requests sequentially using the wordlist entries. 

When it receives a positive response, indicating the formation of a valid URL and, hence, the discovery of a valid directory, it continues to brute-force the remaining directories at the same depth. Only after it has exhausted all directories at the current level does it proceed to brute-force the subdirectories of the discovered directories. This method ensures a thorough search across each level of directories before descending deeper into the directory structure, thereby maximizing the chances of uncovering valuable information distributed across the directories. The majority of commercial tools implement this approach. We also present a pseudocode implementation in Algorithm 2, using a queue to store and retrieve the URLs used during the process. 

Algorithm 2 Breadth-First brute-force attack Pseudocode Figure 2: Visualization of a Weighted Training Tree, obtained merging paths from a Training Dataset. 

1:

procedure BreadthFirst\(𝑟𝑜𝑜𝑡𝑈 𝑅𝐿, 𝑤𝑜𝑟𝑑𝑙𝑖𝑠𝑡 \)

2:

𝑞𝑢𝑒𝑢𝑒 ← new Queue\(\)

3:

𝑞𝑢𝑒𝑢𝑒 .enqueue\(𝑟 𝑜𝑜𝑡𝑈 𝑅𝐿\)

4:

while 𝑞𝑢𝑒𝑢𝑒 is not empty do

\(2\) Constructing a Weighted Wordlist Tree. A weighted tree 5:

𝑐𝑢𝑟 𝑟 𝑒𝑛𝑡𝑈 𝑅𝐿 ← 𝑞𝑢𝑒𝑢𝑒 .dequeue\(\)

using only the words from the wordlist. Starting from a 6:

for each 𝑤𝑜𝑟𝑑 in 𝑤𝑜𝑟𝑑𝑙𝑖𝑠𝑡 do

general wordlist, we construct a weighted tree similar to the 7:

𝑢𝑟 𝑙 ← constructURL\(𝑐𝑢𝑟 𝑟 𝑒𝑛𝑡𝑈 𝑅𝐿, 𝑤𝑜𝑟 𝑑 \)

8:

𝑟 𝑒𝑠 𝑝𝑜𝑛𝑠𝑒 ← sendHTTPrequest\(𝑢𝑟 𝑙 \)

Weighted Training Tree. However, this tree only includes 9:

if isValid\(𝑟𝑒𝑠𝑝𝑜𝑛𝑠𝑒\) then

words from a pre-designed wordlist \(e.g., big\_wfuzz\). The 10:

𝑞𝑢𝑒𝑢𝑒 .enqueue\(𝑢𝑟 𝑙 \)

weight of each node \(directory\) in this tree is determined 11:

end if

12:

end for

based on the training set. For example, if we consider the 13:

end while

wordlist \["news", "home", "2024", "today", "about"\] and the 14:

end procedure

Weighted training tree shown in Figure 2, the corresponding Wordlist Weighted Tree can be visualized in Figure 3. Note that, in this case, folders such as register and weather are 4.2

Probability-based approach

not included in the tree, since they are not contained in the Approach. Prior knowledge might be essential to improve the original wordlist. 

attack performance. The intuition is straightforward: if the majority of websites contain paths like /login and /register, it is likely that the tested website contains such directories as well. 

An algorithm that, therefore, prioritizes directories based on prior knowledge can be effective. 

The first strategy we present optimizes the depth and breadth-first strategies described in Section 4.1, where the wordlist is ordered according to prior knowledge \(e.g., gathered from web applications similar to the victim\). This adds dynamic decisions on how to go about generating the following HT TP request to maximize the number of positive requests while minimizing the number of unlikely and incorrect requests. The prior knowledge, or training dataset, contains crawls of paths of various web applications, possibly of the same category as the target where the attack will be performed. 

The prior knowledge can be then infused into the algorithms in two possible manners:

\(1\) Constructing a Weighted Training Tree. Using the same Figure 3: Visualization of a Wordlist Weighted Tree, based reasoning with which we described how it is possible to on a wordlist and a Weighted training tree. 

reconstruct a filesystem of a web application from the crawl of its paths, we will proceed to construct a single filesystem tree that unites all the paths that contain our training In this way, we can make the best use of parent-child relational dataset indistinctly from the web application. Furthermore, information between directories and subdirectories and give weight this tree will be weighted: for each new node in the tree to words in the wordlist critical for the adaptive selection of requests 187



Offensive AI: Enhancing Directory Brute-forcing Attack with the Use of Language Models AISec ’24, October 14–18, 2024, Salt Lake City, UT, USA to be made. Furthermore, a pruning process can be applied to those the weighted tree have been explored, it is advisable to employ a branches whose 𝑤 is lower than a threshold. The pruning of unlikely conventional breadth-first strategy. This approach takes into ac-words helps, consequently, to minimize the number of less probable count the previously successful responses, thereby mitigating the requests. To give an example of how pruning works, considering need to reissue redundant HT TP requests. 

Figure 2 and Figure 3, we can see that the word "about", which was initially in the wordlist from which the tree is created, is not part 4.3

Language-Model based approach

of the Wordlist weighted tree \(so it has a weight of 0 as a possible Approach. Following the intuition of the probabilistic approach subdirectory for every directory\), and "news" has a weight of 12 as a described in Section 4.2, we design a neural network mechanism subdirectory of the base root, but is pruned from being a child-node leveraging Language Models \(see Section 2\) to generate probable of "home". 

subdirectories to a given path. Given a URL, we can consider its Algorithm. 

path a sequence of words separated by "/." This sequence of words The probabilistic approach employs a max heap \(a can be fed as input to the neural network mechanism, which will data structure that keeps the maximum element of a given property output the words that most likely follow the input sequence. Those on top of it\) with tuples of base URLs, a word, and the weight words can be used to construct new URLs and send new HT TP

assigned to it. The max heap keeps the tuples ordered by probability, requests. 

so we can always pop the highest one to construct and send a With this method, we aim to leverage the power of customized request. The probability of a word being a valid subdirectory of a embeddings \(i.e., embeddings trained on the corpus\), and overcome directory is computed dynamically by dividing the weight of the the limitations of the probabilistic approach. In particular, the prob-possible subdirectory by the sum of the weights of every possible abilistic approach calculates relationships among directories that subdirectory to that directory. 

appear in the prior knowledge. On the other hand, with the embed-In the beginning, given a target base URL, the algorithm will ding, the model learns the context, and therefore directories appear-push in the max heap all the possible subdirectories of the root ing in a similar context will be used to generalize the attack. For directory "/" retrieved from the weighted tree with the correspond-instance, suppose that in our prior knowledge, we have URLs such ing probabilities. Whenever we receive a successful response, the as "/account/setting/info", "/account/setting/password", algorithm pushes all the possible subdirectories to the response

"/account/setting/logout", "/profile/setting/ password" 

URL with the probabilities into the heap. This mechanism allows us and "/profile/setting/info": the directories account and to implement an adaptive decision-making strategy to consistently profile are utilized in a similar context, and therefore their em-send the most likely HT TP request away as new subdirectories are bedding will be close. At inference time, a LM might infer the URL

discovered. 

"/profile/setting/logout" even though this information was An algorithmic exemplification of this approach is presented not available in our prior knowledge. In this example, a probability in the algorithm 3, where getWordswithWeights\(\) returns the approach would have assigned 0 to this association. 

word-weight pairs taken from the specified URL in the weighted tree, and getProbability\(\) calculates the probability of a word Model architecture. Leveraging language models in our architec-as described before. 

ture involves using a crucial component of them: the vocabulary. 

This component maps words in our sequences \(i.e., directories\) to Algorithm 3 Probabilistic brute-force attack Pseudocode unique indexes. The vocabulary allows the translation of words 1:

procedure Probabilistic\(𝑟𝑜𝑜𝑡𝑈 𝑅𝐿, 𝑤𝑒𝑖𝑔ℎ𝑡𝑒𝑑𝑇 𝑟𝑒𝑒\) into integer indices that the neural network architecture can pro-2:

𝑚𝑎𝑥 𝐻 𝑒𝑎𝑝 ← new MaxHeap\(\)

cess. To reduce the dimension of the vocabulary, only words more 3:

𝑟 𝑜𝑜𝑡𝑇 𝑢𝑝𝑙 𝑒𝑠 ← getWordswithWeights \(𝑟 𝑜𝑜𝑡𝑈 𝑅𝐿, 𝑤𝑒𝑖𝑔ℎ𝑡 𝑒𝑑𝑇 𝑟 𝑒𝑒 \) 4:

for each 𝑤𝑜𝑟𝑑, 𝑤𝑒𝑖𝑔ℎ𝑡 in 𝑟𝑜𝑜𝑡𝑇𝑢𝑝𝑙𝑒𝑠 do

frequent than a certain threshold are considered. Additionally, vo-5:

𝑝𝑟 𝑜𝑏 ← getProbability\(𝑤𝑜𝑟 𝑑 , 𝑤𝑒𝑖𝑔ℎ𝑡 , 𝑟 𝑜𝑜𝑡𝑇 𝑢𝑝𝑙 𝑒𝑠 \) cabulary helps the architecture understand the structure of the sen-6:

𝑚𝑎𝑥 𝐻 𝑒𝑎𝑝 .push\(\(𝑟 𝑜𝑜𝑡𝑈 𝑅𝐿, 𝑤𝑜𝑟 𝑑 , 𝑝𝑟 𝑜𝑏𝑎𝑏𝑖𝑙 𝑖𝑡 𝑦 \)\) tences while handling unknown words and variable-size sequences 7:

end for

8:

while 𝑚𝑎𝑥𝐻𝑒𝑎𝑝 is not empty do

with special tokens. These tokens are: UNK \(Unknown word\), PAD

9:

𝑐𝑢𝑟 𝑟 𝑒𝑛𝑡𝑈 𝑅𝐿, 𝑤𝑜𝑟 𝑑 , 𝑝𝑟 𝑜𝑏𝑎𝑏𝑖𝑙 𝑖𝑡 𝑦 ← 𝑚𝑎𝑥 𝐻 𝑒𝑎𝑝 .pop\(\) \(Padding token, used to pad sequences to a fixed size\), SOS \(Start of 10:

𝑢𝑟 𝑙 ← constructURL\(𝑐𝑢𝑟 𝑟 𝑒𝑛𝑡𝑈 𝑅𝐿, 𝑤𝑜𝑟 𝑑 \)

sentence token, used to highlight where a sequence start\) and EOS

11:

𝑟 𝑒𝑠 𝑝𝑜𝑛𝑠𝑒 ← sendHTTPrequest\(𝑢𝑟 𝑙 \)

12:

if isValidURL\(𝑟𝑒𝑠𝑝𝑜𝑛𝑠𝑒\) then

\(End of sentence token, used to highlight where a sequence end\). 

13:

𝑛𝑒 𝑤𝑇 𝑢𝑝𝑙 𝑒𝑠 ← getWordswithWeights\(𝑢𝑟 𝑙 , 𝑤𝑒𝑖𝑔ℎ𝑡 𝑒𝑑𝑇 𝑟 𝑒𝑒 \) Our designed neural network architecture is primarily based 14:

for each 𝑤𝑜𝑟𝑑, 𝑤𝑒𝑖𝑔ℎ𝑡 in 𝑛𝑒𝑤𝑇𝑢𝑝𝑙𝑒𝑠 do

15:

𝑛𝑒 𝑤𝑃 𝑟 𝑜𝑏 ← getProbability\(𝑤𝑜𝑟 𝑑 , 𝑤𝑒𝑖𝑔ℎ𝑡 , 𝑛𝑒 𝑤𝑇 𝑢𝑝𝑙 𝑒𝑠 \) on the Long-Short-Term Memory \(LSTM\) network \[9\], a type of 16:

𝑚𝑎𝑥 𝐻 𝑒𝑎𝑝 .push\(\(𝑢𝑟 𝑙 , 𝑤𝑜𝑟 𝑑 , 𝑛𝑒 𝑤𝑃 𝑟 𝑜𝑏 \)\)

Recurrent Neural Network. Our proposed LM architecture consists 17:

end for

of several key components:

18:

end if

19:

end while

\(1\) Embedding Layer. The first layer of the model is an em-20:

end procedure

bedding layer, which transforms the input words into dense vectors of fixed size, defined as embedded size. Embedding Because of aggressive pruning on the wordlist tree or due to a representations are learned at training time. 

training dataset that does not contain as much data, the possible \(2\) LSTM Layer. It follows a LSTM layer, crucial for the learning requests provided by the weighted tree will be exhausted quickly, of patterns in sequential data. This layer takes the embed-even before reaching any set request budget. In light of this, when dings of the input words and returns its own hidden states all potential requests derived from the existing knowledge within and cell states. 

188



AISec ’24, October 14–18, 2024, Salt Lake City, UT, USA Alberto Castagnaro, Mauro Conti, & Luca Pajola \(3\) Dropout Layer. To prevent overfitting, dropout layers are Algorithm 4 Language-model based brute-force attack Pseudocode used after the Embedding and LSTM layers. Dropout is a 1:

procedure LMattack\(𝑟𝑜𝑜𝑡𝑈 𝑅𝐿, 𝐿𝑀, 𝑡𝑜𝑝𝑃𝑟𝑒𝑑𝑖𝑐𝑡𝑠\)

regularization technique that randomly sets a fraction of 2:

𝑚𝑎𝑥 𝐻 𝑒𝑎𝑝 ← new MaxHeap\(\)

3:

𝑟 𝑜𝑜𝑡𝑇 𝑢𝑝𝑙 𝑒𝑠 ← predict\(𝑟 𝑜𝑜𝑡𝑈 𝑅𝐿, 𝐿𝑀 ,𝑡𝑜𝑝𝑃 𝑟 𝑒𝑑𝑖𝑐𝑡 𝑠 \) input units to 0 with a specific frequency of rate at each step 4:

for each 𝑤𝑜𝑟𝑑, 𝑝𝑟𝑜𝑏 in 𝑟𝑜𝑜𝑡𝑇𝑢𝑝𝑙𝑒𝑠 do

during the training. 

5:

𝑚𝑎𝑥 𝐻 𝑒𝑎𝑝 .push\(\(𝑟 𝑜𝑜𝑡𝑈 𝑅𝐿, 𝑤𝑜𝑟 𝑑 , 𝑝𝑟 𝑜𝑏 \)\)

6:

end for

\(4\) Fully Connected Layer: The LSTM outputs \(hidden states\) 7:

while 𝑚𝑎𝑥𝐻𝑒𝑎𝑝 is not empty do

are then passed through a fully connected \(linear\) layer to 8:

𝑐𝑢𝑟 𝑟 𝑒𝑛𝑡𝑈 𝑅𝐿, 𝑤𝑜𝑟 𝑑 , 𝑝𝑟 𝑜𝑏 ← 𝑚𝑎𝑥 𝐻 𝑒𝑎𝑝 .pop\(\) transform them into the desired output shape, which is the 9:

𝑢𝑟 𝑙 ← constructURL\(𝑐𝑢𝑟 𝑟 𝑒𝑛𝑡𝑈 𝑅𝐿, 𝑤𝑜𝑟 𝑑 \)

10:

𝑟 𝑒𝑠 𝑝𝑜𝑛𝑠𝑒 ← sendHTTPrequest\(𝑢𝑟 𝑙 \)

size of the vocabulary. 

11:

if isValidURL\(𝑟𝑒𝑠𝑝𝑜𝑛𝑠𝑒\) then

\(5\) Softmax Function: A softmax function is applied to trans-12:

𝑛𝑒 𝑤𝑇 𝑢𝑝𝑙 𝑒𝑠 ← predict\(𝑢𝑟 𝑙 , 𝐿𝑀 ,𝑡𝑜𝑝𝑃 𝑟 𝑒𝑑𝑖𝑐𝑡 𝑠 \) form the output of the fully connected layer to probabilities 13:

for each 𝑤𝑜𝑟𝑑, 𝑛𝑒𝑤𝑃𝑟𝑜𝑏 in 𝑛𝑒𝑤𝑇𝑢𝑝𝑙𝑒𝑠 do

14:

𝑚𝑎𝑥 𝐻 𝑒𝑎𝑝 .push\(\(𝑢𝑟 𝑙 , 𝑤𝑜𝑟 𝑑 , 𝑛𝑒 𝑤𝑃 𝑟 𝑜𝑏 \)\)

assigned to each vocabulary word. 

15:

end for

Figure 4 shows an overview of the architecture. Here, we can 16:

end if

17:

end while

see how the URL path is split into tokens and mapped into integers 18:

end procedure

using vocabulary. Then, after the sequence of integers is given as input to the model, we observe how the softmax function takes the output of the fully connected layer and assigns the probability that also aligns with ethical considerations, avoiding manual spidering it is the next in the sequence to each number. At this point, the and crawling of websites that may be categorized as brute-force most likely word is chosen to form a new path, but the choice can attacks and not overloading web servers with severe amounts of also be made on any other word. 

requests but instead using historical data. Given the scope of the Training and Validation. 

search and the multitude of data in the CommonCrawl corpus, we Our architecture’s training process in-collected the URLs from the HT TP responses. We then extracted volves feeding it with paths and having it predict the following the domain, path, and response code necessary to identify invalid directory in the path. The model’s predictions are compared to the responses. 

actual following directories in the path, and a loss function is used to quantify the difference between the predictions and the truth. This Datasets. Considering the increasing number of cyber attacks loss is minimized using an optimization algorithm, which adjusts and the wide variety of possible targets, we decided to consider the model’s parameters to make its predictions more accurate. 

four different datasets representing some most common categories During the training phase, the model performance is periodically of organizations at risk of cyber attacks \[7, 19\]. In addition, given evaluated on the validation set to prevent overfitting on training the scope of the search, we maintained only websites written in data. This strategy allows us to monitor the model’s generalization English. We now list the four distinct datasets we collected: ability to unseen data. We utilize an early stopping mechanism to

• Universities dataset \[UNI\]: consisting of the HTTP responses stop the training when the model’s performance on the validation from 100 English-based web applications of the top univer-set starts to deteriorate \(a phenomenon known as overfitting\) or

7

sities listed in the QS 2023 World University Rankings

. 

does not improve for 𝑝 epochs. 

Furthermore, we did not consider universities without an Algorithm. The algorithm incorporating the proposed neural English version of their web application. 

network architecture \(Algorithm 4\) uses a strategy similar to Algo-

• Hospitals dataset \[HOS\]: consisting of the HTTP responses rithm 3, where a max heap is used to construct the most probable belonging to the web applications of the first USA 100 hos-

8

URL. Instead of using the wordlist weighted tree, the language pitals listed in "Ranking Web of World Hospitals" 

. 

model in the function predict\(\) is used to return a number of

• Companies dataset \[COM\]: consisting of the HTTP responses word-probability pairs with a higher probability specified in the from 100 corporate web applications of companies in the S&P

topPredicts

9

hyper-parameter. 

500

, choosing in order of highest capitalization \( January 2024\) and avoiding companies that had e-commerce as their 5

Dataset

main web application. 

In this section, we present the datasets collected for our experiments. 

• Government dataset \[GOV\]: consisting of the HTTP responses

10

In particular, Section 5.1 describes the data collection process. It from 336 different USA government web applications

. 

follows Section 5.2, presenting an in-depth analysis of our data. 

In our experiments, we will report the attack performance when considering the datasets separately and together. 

5.1

Description

Preprocessing. After extracting the domain, path, and status code Source of data. The data for this research is obtained from Com-from each HT TP response for each dataset, we performed addi-

6

monCrawl

, a non-profit organization that crawls the web and tional preprocessing steps on the data to reconstruct the hierarchical freely provides its archives and datasets. CommonCrawl was se-structure of the file system of the Web applications, guaranteeing lected due to its comprehensive repository of web crawls that are updated regularly; we utilized CC-MAIN-2023-40 crawl version. 

7 https://www.topuniversities.com/world-university-rankings/2023

8

This approach not only streamlines the data collection process but

https://hospitals.webometrics.info/en/americas/usa

9 https://www.slickcharts.com/sp500

6

10

https://commoncrawl.org/

https://www.usa.gov/agency- index

189



Offensive AI: Enhancing Directory Brute-forcing Attack with the Use of Language Models AISec ’24, October 14–18, 2024, Salt Lake City, UT, USA Figure 4: Prediction of the next directory from our LM-based architecture. 

their integrity and enabling more consistent analysis in the datasets. 

• Number of paths in each dataset \(\# Paths\). For instance, Firstly, we applied initial filtering to the HT TP responses, preserv-suppose a dataset contains two web apps, each with one ing only the responses with a status code 200, representing most domain \(e.g., "domain1/login" and "domain2/login"\), the of the crawled responses. The HT TP status code 200 indicates that number of paths is two, i.e., \["/login", "/login"\]\). 

the client request has succeeded. Secondly, eventual queries or files

• The average number \(and standard deviation\) of paths of the that were part of the path were removed. This choice was mainly web apps contained in a given dataset \(\# paths AVG and made to maintain a manageable scope of analysis. URLs can often

\# paths STD\). For instance, given two web apps containing contain queries or files with different extensions that introduce a each 1 URLs, the average is equal to 1, and the standard significant degree of variability and are highly dependent on the deviation to 0. 

technology with which the web application was developed, thus

• The number of unique paths in the dataset \(\# U-Paths\). For going against our intended general approach. Additionally, it is use-instance, suppose the dataset contains the following samples ful to define the depth of a path: considering a path as a sequence

" domain1/account/info " and " domain2/account/ info", of words \(where each word corresponds to the name of a directory\), the unique paths are defined as the unique path \["/account/info"\]. 

we define the depth as the number of words that the path consists

• The number of directories \(\# Dir\) contained in the dataset. 

of. The order matters since each directory in that path will be at a For instance, given "domain1/account/info" and "domain2

given depth \(e.g.: "/news/2023" will have depth = 2, where "news" 

/account/settings", the dataset contains four directories is at depth 1, and "2023" is at depth 2\). 

\["account", "info", "account", "settings"\]. 

• The number of unique directories \(\# U-Dir\) contained in the 5.2

Datasets Analyses

dataset. For instance, given "domain1/account/info" and

"domain2/account/settings", the dataset contains three Overview. Following the data preprocessing, we analyzed the unique directories \["account", "info", "settings"\]. 

characteristics of each dataset and the similarities and differences

• We analyze the depth of URLs in terms of average and stan-between them, which allowed us to get a general overview of the dard deviation \(Depth AVG and Depth STD\). For instance, datasets and highlight what direction the test results might take. 

the URL "domain1/account/info" has a depth equal to two. 

We conduct the following analyses:

Hypothesizing that a directory with greater depth is likely

• Dataset description, where we describe datasets’ properties to be more specialized and, consequently, less common, ana-

\(e.g., quantities, distributions\) and the nature of their URLs. 

lyzing depth distribution might provide insight into a web

• Wordlist Coverage Ratio Analysis, where we describe how application’s granularity and structure. 

standard wordlists can cover the retrieved URLs. 

• The average depth and standard deviation of URLs similari-

• Stemming Analysis, where we attempt to understand the ties in a given dataset \(Sim AVG and Sim STD\). In more detail, impact of small name variations in the directories \(e.g., books this metric computes the similarity for each pair of websites and book\) and wordlists coverage. 

in each dataset. By defining a website as a set of its own

• Dataset Similarity Analysis, where we describe the degree of directories \(computed by the retrieved URLs\), the similarity similarity between directories in the four collected datasets between two websites can be computed using the Jaccard \(e.g., how universities and hospital URLs differ\). 

Similarity, defined in Equation 6. This metric is defined be-We report below only the dataset description, while in-depth tween 0 and 1, where 0 means that two sets are distinct, analyses can be found in Appendix A. 

while one means identical. 

|𝐴 ∩ 𝐵|

5.2.1

Dataset description. 

𝐽 \(𝐴, 𝐵\) =

. 

\(6\)

We now describe the four distinct datasets

|𝐴 ∪ 𝐵|

we retrieved. For each dataset, we analyzed the following informa-Table 1 shows the statistics for each dataset. We highlight that tion:

not all scraped domains contained the HT TP status code 200, and

• Number of domains \(\# Domains\). 

therefore they are not present. This justify the discrepancy between 190



AISec ’24, October 14–18, 2024, Salt Lake City, UT, USA Alberto Castagnaro, Mauro Conti, & Luca Pajola the number of scraped domains and the actual domain \(e.g., the LM validation. We utilize PyTorch \[15\] to design our architecture. 

dataset contains URLs from 88 universities and not 100\). 

LM uses the training set to learn meaningful association, while the validation set is utilized to select the best LM hyperparameters. 

Dataset

For the model selection, we use a grid-search validation over the features

UNI

HOS

COM

GOV

following hyper-parameters. 

\# Domains

88

80

97

336

• Data representation. We identify hyper-parameters that con-

\# Paths

209657

211911

147198

520571

trols the training input: the maximum length of the paths

\# Paths AVG

2301

2584

1479

1507

\# Paths STD

2906

2800

2360

2340

utilized in the training phase and the minimum frequency

\# U-Paths

201768

205587

143067

502693

that a directory must have not to be discarded and marked as

\# Dir

203613

209945

143620

512595

"Unknown." For the former, defined as max\_depth, we chose

\# U-Dir

171215

173394

106097

462812

Depth AVG

4.11

3.31

4.43

3.40

values \[5, 10\], while for the latter, defined as min\_freq, we Depth STD

1.69

1.72

2.23

1.66

chose \[3, 5\]. 

Sim AVG

0.022

0.019

0.016

0.016

Sim STD

0.031

0.017

0.023

0.024

• LM architecture. embedding\_size \[ES\] = \[128, 256, 512\], Table 1: Statistics for the datasets: universities \[UNI\], hospi-n\_layers \[NL\] \(number of layers in the LSTM\) = \[2, 3, 4\], tals \[HOS\], companies \[COM\], government \[GOV\]. 

dropout\_rate \[DR\]=\[0.2, 0.4, 0.6\]. 

An early stopping mechanism is set with patience equal to 10 epochs. 

The learning phase uses Adam \[11\] as optimizer, and CrossEntropy as loss function. Finally, the best model is chosen based on the Discussions. It is interesting to observe that websites have differ-lower loss at the validation set. In addition, we tested an additional ent structures in terms of number of pages. For instance, universities parameter, namely the number of predictions to be considered and hospitals tend to have a bigger number of pages \(\# Path AVG\) whenever a positive response is received during the attack and new compared to companies and governments. From a depth perspec-predictions are made. The parameter, defined as topPredicts in tive, university and company websites tend to have deeper web Algorithm 4, is tested with the values \[100, 250, 500, 750, 1000, 2000, app structures compared to hospitals and government. Last, the 5000, 10000\]. 

similarity analysis clearly shows that websites in the same dataset tend to have different types of directories, and the average Jaccard Evaluation Metric. We utilize the following evaluation metrics: similarity tends to zero. By considering these statistics together, we

•

can clearly remark why directory enumeration is not trivial, and it Average Successful Response Rate, consisting of averaging the might require an enormous amount of requests for a small number total amount of successfully discovered directories for each of hits \(i.e., discovered directories\). 

tested website. 

• Bins efficiency, consisting of averaging the total amount of 6

Evaluation

successfully discovered directories for each tested website 6.1

Experimental Settings

in a given range of requests. We evaluate the following bins: 0-100, 101-1000, 1001-10000, 10001-50000, and 50001-100000. 

Testbed. To set up our brute-force directory attack simulations, We did not consider execution times as they depend on various we partitioned the datasets into distinct sets for training, validation, factors \(such as the number of threads used in the attack and time and testing. We train our proposed approaches \(i.e., probabilistic between request and response variable for each application\) and and LM-based\) in a training set that merges the four presented are not quantifiable with offline simulations. 

in Section 5.1. Merging the four data sources for the training is essential to have a sufficient number of samples to train a LM with. 

We, therefore, merge the four datasets and divide them into training, 6.2

Results

validation, and testing sets with a 70-10-20 split ratio, as mentioned Overview. Table 2 shows the overall results obtained in our ex-in Section 4.3. Note that the split is not random in terms of URLs, periments, at the varying of the dataset, wordlists, and inference but from a domain perspective. In this way, all URLs of a given techniques. LM-based attack outperforms all the other baselines website will appear only in training, validation, or testing set. With in all datasets, demonstrating the superiority of language mod-this approach, we avoid any data snooping \[3\]. 

els compared to naive techniques like brute-force or probabilistic Regarding the testing environment, we opted to simulate brute-approaches. Interestingly, LM’s performances are not equally bal-force attacks offline, utilizing the virtual filesystems reconstructed anced on all datasets: for instance, LM struggles with university from the test applications. This approach permits executing multi-and company websites, while being robust with hospital and gov-ple attack simulations using different strategies without actualizing ernment ones. The probabilistic-based approach further shows a real-time brute-force attacks on live web applications. Furthermore, good improvement over brute-force attacks since, with a limited this approach allows us to work with a high number of simulated budget, the latter might not be able to fully assess all the possibil-requests without introducing latency due to the HT TP requests. 

ities. On the other hand, probabilistic approaches, by optimizing Additionally, aligning with our objective to maximize successful the priorities of the requests, are more efficient. 

responses while minimizing request volume, we established a maximum budget of 100,000 requests spendable by each simulated attack Bins efficiency. The efficiency analysis provides another interest-before termination. 

ing perspective on how different approaches perform. We analyze 191





Offensive AI: Enhancing Directory Brute-forcing Attack with the Use of Language Models AISec ’24, October 14–18, 2024, Salt Lake City, UT, USA Wordlist

Dataset

analyze how the best LM found changes its performance at the UNI

HOS

COM

GOV

ALL

Breadth

varying of this setting. In particular, we explore the following: 100, big\_wfuzz

28.0

22.0

27.0

35.0

35.0

250, 500, 750, 1000, 2000, 5000, and 10000. As shown in Figure 6, 

directory-list\_dirbuster

8.0

10.3

9.6

11.8

10.5

as the number of predictions considered increases, the average megabeast\_wfuzz

10.5

11.6

11.0

12.4

11.7

number of successful responses received in the attack simulations top\_10k\_github

21.3

42.6

26.8

27.0

28.6

Depth

decreases. In addition, although with a smaller topPredicts the big\_wfuzz

28.0

22.0

27.0

33.0

33.0

initial average number of successful responses received is better, the directory-list\_dirbuster

0.5

0.5

0.7

0.4

0.5

megabeast\_wfuzz

2.6

2.9

2.7

2.7

2.7

simulations end earlier as they have no more new predictions with top\_10k\_github

10.1

10.1

10.1

10.0

10.1

which to send new requests. It is, therefore, essential to consider a Probability

value for this parameter that maximizes the results and utilizes the big\_wfuzz

28.0

22.0

27.0

34.5

34.5

directory-list\_dirbuster

14.0

13.1

11.1

17.3

25.4

entire predetermined request budget. Therefore, it might be ideal megabeast\_wfuzz

12.5

13.9

11.8

13.8

13.8

to set topPredicts to a small number if our budget is limited, as top\_10k\_github

23.4

42.9

26.1

27.1

26.7

the model reaches the most successful responses in a short time. 

train-set

31.9

60.4

27.6

30.8

42.5

LM

On the opposite, larger numbers like 500, 750, and 1000 are ideal train-set

90.0

175.0

89.0

128.0

175.0

when the budget allows an exhaustive search. 

Table 2: Average successful responses for each approach achieved for different test-sets at the varying of the datasets. 

In bold the best results. 

the efficiency shown in Figure 5, calculated by considering simulations on the general test dataset \(\[ALL\]\) and on the wordlist big\_wfuzz. 

Although the mean results obtained using the breadth, depth, and probabilistic approaches are the same, the efficiency varies considerably. The probabilistic approach performs very well in initial requests and then declines as requests increase. Although the language model approach registers a 400% increase in average successful responses, it performs worse in initial requests than the probabilistic approach but is more efficient in the long run. This behaviour between the two is also observable in the other cases. 

Therefore, adopting a probabilistic approach might be ideal when the budget is more limited. 

Figure 6: Evolution of average successful responses for different topPredicts values

Results analysis. The two proposed approaches show substantial improvements in both metrics examined. Of the two standard approaches, the breadth-first strategy \(also implemented by commercial tools\) emerges as the best. 

The probabilistic approach improves the performance of the breadth-first approach in 65% of the cases considering the four default wordlists, while in the remaining, it obtains equal or slightly lower results. Depth-first approaches are outperformed in 100% of the cases. In particular, if we consider the breadth-first approach, the probability-based approach using the train-set wordlist has the Figure 5: Mean Efficiency Ratio of the four approaches on following average improvements: University \+141%, hospital \+281%, different bins, considering wordlist = **big\_wfuzz **and the gen-companies \+85%, government \+78%, and ALL \+159%. The strength eral dataset. 

of this approach is the efficiency of successful responses received using few requests, which outperforms all other approaches considerably. The Language-based approach outperforms the standard 6.3

Discussion

approach in 100% of the simulations. The LM-based model approach The impact of topPredicts. Algorithm 4 relies on many hyper-has the following average improvements over the breadth-first parameters, such as topPredicts. It controls the number of most baselines: University \+582%, hospital \+1004%, companies \+499%, likely predictions to be considered in each new folder found. We government \+639%, and ALL \+969%. 

192



AISec ’24, October 14–18, 2024, Salt Lake City, UT, USA Alberto Castagnaro, Mauro Conti, & Luca Pajola Embeddings similarity. The ability of embeddings to extract con-al. \[5\] demonstrated the potential of AI-generated fingerprint deep-text from web application paths and generalize is essential to predict fakes to compromise biometric systems through dictionary attacks, valid directories and URLs. The results, especially in simulations on highlighting the vulnerability of such systems to sophisticated AI general test sets, highlight how the Language model approach suc-techniques. Al-Hababi et al. \[1\] investigated man-in-the-middle at-cessfully uses the context extrapolated from embeddings to achieve tacks leveraging machine learning to identify services in encrypted significantly better results than the other approaches. 

network flows. Li et al. \[12\] presented a generative adversarial net-We can observe this by reporting two examples: given two di-work designed to evade PDF malware classifiers, illustrating the rectories, we use the Cosine similarity to measure the top 10 words ease with which AI can bypass traditional cybersecurity defences. 

most similar directories, which should belong to a similar context: Nam et al. \[14\] developed a recurrent GANs-based password cracker aimed at enhancing IoT password security. While intended for de-

\(1\) article: \(’stories’, 0.48\), \(’academics’, 0.43\), \(’press-release’, fensive purposes, the study also signifies how AI can be repurposed 0.39\), \(’press-releases’, 0.38\), \(’video’, 0.32\), \(’authors’, 0.32\), for

\(’spotlight’, 0.32\), \(’articles’, 0.31\), \(’case’, 0.3\), \(’impact’, 0.29\) \(2\) about: \(’locations’, 0.79\), \(’about-us’, 0.75\), \(’research’, 0.75\), \(’programs’, 0.74\), \(’conditions’, 0.7\), \(’services’, 0.68\), \(’re-8

Conclusions

sources’, 0.68\), \(’alumni’, 0.68\), \(’careers’, 0.67\), \(’contact’, Current directory brute-forcing attacks are notoriously inefficient 0.66\)

since they rely on brute-forcing strategies, resulting in an enor-In both cases, we can see that the words determined similarly by the mous amount of queries for a few successful discoveries. In this embeddings represent the same word but slightly different, such as work, we investigated whether the utilization of prior knowledge

’about’ with ’about-us’ or ’article’ with ’articles’. In addition, might result in more efficient attacks. We propose two distinct we find other words that relate to the context created by the word methods that rely on prior knowledge: a probabilistic model and under consideration, such as ’authors’ or ’stories’ for ’article. 

a Language Model-based attack. We then experimented with our This outcome confirms the superiority of LM in generalizing the proposed methodology in a dataset containing more than 1 million observed pattern at training time. 

URLs, spanning across distinct web app domains such as universi-Examples of LM Patterns. 

ties, hospitals, companies, and government. Our results show the The high average number of successful

superiority of the proposed method, with the LM-based approach responses obtained from the LM-based approach testifies to the outperforming brute-force-based approaches in all scenarios \(an model’s ability to predict valid directories that follow recurring pat-average performance increase of 969%\). Furthermore, the simple terns. For example, let us examine the Language model’s predictions probabilistic approach results effective when the budget of requests on two different URLs:

is limited \(below 100, for stealthier attacks\). The research presented \(1\) URL: /campus-life-events/calendar. Among the top 10 direc-in this paper lays the groundwork for several promising directions tories predicted with this URL, we have \[’05’, ’06’, ’08’, ’11’, for future investigation. The use of Artificial Intelligence to cre-

’may’, jun’\], which refer to days or months of a calendar. 

ate sophisticated attacks is a topic that is constantly evolving and \(2\) URL: /media. Among the top directories predicted with this growing in cybersecurity, especially with the fast development of URL, we have \[’press-releases’, ’news’\] that are found in Language models. 

multiple paths in the training dataset and that refers to a Future work could explore improvements of our LM-based archi-similar context. 

tecture, such as attention mechanisms \[20\], or even Large Language Models \[6\]. These models’ enhanced understanding of context and 7

Related Work

semantics could significantly refine the process of predicting web The emergence of offensive AI in cybersecurity presents a new application structures. Additionally, a path that may be explored is frontier where artificial intelligence \(AI\) is leveraged to create so-the development of a language model trained explicitly on paths phisticated and automated attacks and enhance the penetration and files commonly associated with vulnerabilities. By focusing testing process \[10, 13\]. These attacks represent a new landscape on these critical areas, the model could help preemptively identify that poses significant challenges and opportunities in cybersecurity, potential security risks, thereby contributing to more proactive especially with the raising of LLMs and generative AI. 

cybersecurity measures and showing the feasibility of such attacks. 

The use of generative AI to enhance directory brute-forcing at-These areas of future work offer the potential to significantly tacks has yet to be explored. The closest attempt is presented by He impact the development of more secure web environments and et al. \[8\], where the authors proposed an attack to medical systems pose new security challenges to language model usage. 

by adopting semantic clustering of sentences. No much information are reported in terms of data, methodology, and results. Similarly, 9

Acknowledgment

Antonelly et al. \[2\] presented an innovative approach using the Universal Sentence Encoder \(USE\) for semantic analysis. The K-This work was supported by the European Commission under the means algorithm and the elbow method were used for clustering to Horizon Europe Programme, as part of the project LAZARUS \(https:

optimize directory brute-forcing \(dirbusting\), with an improvement

//lazarus- he.eu/\) \(Grant Agreement no. 101070303\). The content in the results of up to 50% on only eight web applications tested. 

of this article does not reflect the official opinion of the European Several other studies have analyzed the threat that offensive Union. Responsibility for the information and views expressed AI poses to organizations in other types of attacks. Bontrager et therein lies entirely with the authors. 

193



Offensive AI: Enhancing Directory Brute-forcing Attack with the Use of Language Models AISec ’24, October 14–18, 2024, Salt Lake City, UT, USA References

A

Dataset Analyses

\[1\]

Abdulrahman Al-Hababi and Sezer C Tokgoz. 2020. Man-in-the-middle attacks to A.1

Wordlists Coverage Ratio Analysis

detect and identify services in encrypted network flows using machine learning. 

In 2020 3rd International Conference on Advanced Communication Technologies By analyzing the coverage of the different wordlists on the web and Networking \(CommNet\). IEEE, 1–5. 

applications in each dataset, shown in Figure 7, we can see that a

\[2\]

Diego Antonelli, Roberta Cascella, Gaetano Perrone, Simon Pietro Romano, and Antonio Schiano. 2021. Leveraging AI to optimize website structure discovery low percentage of words are found even at low depths where we during Penetration Testing. 

arXiv:2101.07223 \[cs.CR\]

would expect them to be more common and thus present in the

\[3\]

Daniel Arp, Erwin Quiring, Feargus Pendlebury, Alexander Warnecke, Fabio wordlist. 

Pierazzi, Christian Wressnegger, Lorenzo Cavallaro, and Konrad Rieck. 2022. Dos and don’ts of machine learning in computer security. In 31st USENIX Security The coverage ratio across the different datasets shows consid-Symposium \(USENIX Security 22\). 3971–3988. 

erable variance but overall low values, highlighting how directory

\[4\]

Steven Bird, Ewan Klein, and Edward Loper. 2009. Natural language processing with Python: analyzing text with the natural language toolkit. " O’Reilly Media, brute-force attacks using these wordlists could potentially miss Inc.". 

multiple valid requests. 

\[5\]

Philip Bontrager, Aditi Roy, Julian Togelius, Nasir Memon, and Arun Ross. 2018. 

Although the coverage ratio shows an upward trend as depth Deepmasterprints: Generating masterprints for dictionary attacks via latent variable evolution. In 2018 IEEE 9th International Conference on Biometrics Theory, increases, it is essential to emphasize that although the higher-Applications and Systems \(BTAS\). IEEE, 1–9. 

depth words might be more specific, their number is significantly

\[6\]

Yupeng Chang, Xu Wang, Jindong Wang, Yuan Wu, Linyi Yang, Kaijie Zhu, Hao reduced \(as highlighted by the depth distribution analyzed earlier\). 

Chen, Xiaoyuan Yi, Cunxiang Wang, Yidong Wang, et al. 2023. 

A survey on

evaluation of large language models. ACM Transactions on Intelligent Systems In addition, the most critical point concerns the poor coverage of and Technology \(2023\). 

the initial words, which form the basis of most pathways: higher-

\[7\]

Abrael Delgado. 2023. 

Who is the Prime Target for Cyber Attacks? — compuquip.com. https://www.compuquip.com/blog/prime- target- for- cyber- attacks-

depth directories will not be explored if antecedent ones are not

and- to- look- out- for. 

\[Accessed 10-05-2024\]. 

explored. 

\[8\]

Ying He, Cunjin Luo, Jiyuan Zheng, Kuanquan Wang, and Henggui Zhang. 2022. 

AI Based Directory Discovery Attack and Prevention of the Medical Systems. In 2022 Computing in Cardiology \(CinC\), Vol. 498. IEEE, 1–4. 

A.2

Stemming Analysis

\[9\]

Sepp Hochreiter and Jürgen Schmidhuber. 1997. Long short-term memory. Neural computation 9, 8 \(1997\), 1735–1780. 

Stemming is a linguistic process that simplifies words to their base

\[10\]

Nektaria Kaloudi and Jingyue Li. 2020. The ai-based cyber threat landscape: A or root form, known as the stem, often by removing common pre-survey. ACM Computing Surveys \(CSUR\) 53, 1 \(2020\), 1–34. 

fixes or suffixes. For example, stemming removes plural \(dogs −

→

\[11\]

Diederik P. Kingma and Jimmy Ba. 2015. Adam: A Method for Stochastic Optimization. In 3rd International Conference on Learning Representations, ICLR 2015, dog\), -ing form \(running −

→ run\), etc. In our study, we employed the

San Diego, CA, USA, May 7-9, 2015, Conference Track Proceedings, Yoshua Bengio Porter-Stemmer \[4\] algorithm to analyze the effect of stemming on and Yann LeCun \(Eds.\). 

http://arxiv.org/abs/1412.6980

the total number of unique words within our datasets. In our analy-

\[12\]

Yuanzhang Li, Yaxiao Wang, Ye Wang, Lishan Ke, and Yu-an Tan. 2020. 

A

feature-vector generative adversarial network for evading PDF malware classi-sis, we found a few instances of how a root form represents minimal fiers. Information Sciences 523 \(2020\), 38–48. 

variations of the same word, highlighting different conventions or

\[13\]

Yisroel Mirsky, Ambra Demontis, Jaidip Kotak, Ram Shankar, Deng Gelei, Liu Yang, Xiangyu Zhang, Maura Pintor, Wenke Lee, Yuval Elovici, et al. 2023. The singular and plural forms. A pair of examples are: threat of offensive ai to organizations. Computers & Security 124 \(2023\), 103006. 

\(1\) "articl" corresponding to "article" in 33.5% of cases, "articles" 

\[14\]

Sungyup Nam, Seungho Jeon, Hongkyo Kim, and Jongsub Moon. 2020. Recurrent gans password cracker for iot password security enhancement. Sensors 20, 11

in 14.4%, "Article" in 47.3%, "Articles" in 4.7%, and "ARTICLE" 

\(2020\), 3106. 

in 0.01%. 

\[15\]

Adam Paszke, Sam Gross, Francisco Massa, Adam Lerer, James Bradbury, Gregory Chanan, Trevor Killeen, Zeming Lin, Natalia Gimelshein, Luca Antiga, Alban \(2\) "project" corresponding to "project" in 46.78% of cases , "projects" 

Desmaison, Andreas Köpf, Edward Yang, Zach DeVito, Martin Raison, Alykhan in 53.13, "Projected" in 0.04% and "Projects" in 0.04%. 

Tejani, Sasank Chilamkurthy, Benoit Steiner, Lu Fang, Junjie Bai, and Soumith Chintala. 2019. 

PyTorch: an imperative style, high-performance deep learning However, these represent only a minority of cases, as most root library. Curran Associates Inc. 

forms correspond to only one word, and the percentage reduction

\[16\]

Jeffrey Pennington, Richard Socher, and Christopher D Manning. 2014. Glove: Global vectors for word representation. In Proceedings of the 2014 conference on in the datasets remains marginal, as shown in Table 3. These sta-empirical methods in natural language processing \(EMNLP\). 1532–1543. 

tistics highlight how the words that make up our directory list

\[17\]

Fabio Petroni, Tim Rocktäschel, Sebastian Riedel, Patrick Lewis, Anton Bakhtin, differ \(although some words have various declinations\) and how Yuxiang Wu, and Alexander Miller. 2019. Language Models as Knowledge Bases?. 

In Proceedings of the 2019 Conference on Empirical Methods in Natural Language that should be taken into account when designing new, improved Processing and the 9th International Joint Conference on Natural Language Pro-approaches. 

cessing \(EMNLP-IJCNLP\), Kentaro Inui, Jing Jiang, Vincent Ng, and Xiaojun Wan \(Eds.\). Association for Computational Linguistics, Hong Kong, China, 2463–2473. 

https://doi.org/10.18653/v1/D19- 1250

\[18\]

Tobias Schnabel, Igor Labutov, David Mimno, and Thorsten Joachims. 2015. 

Dataset

Evaluation methods for unsupervised word embeddings. In Proceedings of the 2015 conference on empirical methods in natural language processing features

UNI

HOS

COM

GOV

. 298–307. 

\[19\]

The Constella Team. 2022. Top Common Targets for Hackers | How Do Hackers

\# U-Dir

171215

173394

106097

462812

Choose Targets? — constella.ai. 

https://constella.ai/top- common- targets- for-

\# U-Root

168462

171371

104220

457912

hackers/. 

\[Accessed 10-05-2024\]. 

Reduction

2753

2023

1877

4900

\[20\]

Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Reduction \(%\)

1.61%

1.17%

1.77%

1.06%

Aidan N Gomez, Łukasz Kaiser, and Illia Polosukhin. 2017. 

Attention is all

Table 3: Summary statistics after the STEMMING for the you need. Advances in neural information processing systems 30 \(2017\). 

four datasets: universities \[UNI\], hospitals \[HOS\], companies

\[COM\], and government \[GOV\]. 

194



AISec ’24, October 14–18, 2024, Salt Lake City, UT, USA Alberto Castagnaro, Mauro Conti, & Luca Pajola 0.4

0.4

0.4

0.4

MW

MW

MW

MW

0.3

BW

BW

BW

BW

atio

0.3

0.3

0.3

DB

atio

DB

atio

DB

atio

DB

0.2

GH

0.2

GH

0.2

GH

0.2

GH

0.1

Coverage R

0.1

Coverage R

0.1

Coverage R

0.1

Coverage R

0.0

2

4

6

8

10

0.0

2

4

6

8

10

0.0

2

4

6

8

10

0.0

2

4

6

8

10

Depth

Depth

Depth

Depth

\(a\) University. 

\(b\) Hospital. 

\(c\) Company. 

\(d\) Government. 

Figure 7: Coverage analysis at the varying of the four datasets and four wordlists. Datasets: universities \[UNI\], hospitals \[HOS\], companies \[COM\], and government \[GOV\]. Wordlists: **big\_wfuzz **\[BW\], **top\_10k\_github **\[GH\], **megabeast\_wfuzz **\[MW\], and **directory-list\_dirbuster **\[DB\]. 

A.3

Similarity Analysis

Last, we measure the similarity between any pair of the collected UNI

UNI

dataset. We utilize two metrics: the Jaccard similarity of each dataset HOS

0.013

947

wordlist, and the number of paths in common \(relative number\) HOS

0.009

0.008

between the datasets. Figure 8 shows the results. The first clear COM

COM

662

883

outcome is highlighted by the low Jaccard similarities: each dataset VGO 0.012 0.009 0.008

V

1792

2235

3531

contains different directories. In other words, how websites of uni-UNI

HOS

COM

GOV

GO

UNI

HOS

COM

GOV

versities have almost completely different structures compared to hospital ones. This reasoning can be applied to any pair of datasets \(a\) Jaccard similarities between \(b\) Number of common paths. 

we utilized. A second interesting outcome is given by the relative datasets wordlist. 

count of common directories among different datasets. For instance, government and company websites contain many common paths. 

Figure 8: Similarity analysis for the four dataset: universities Considering the number of unique directories shown in Table 1, it

\[UNI\], hospitals \[HOS\], companies \[COM\], and government is clear that it is non trivial to design an effective directory enumer-

\[GOV\]. 

ation brute-force attack. 

195



# Document Outline

+ Abstract 
+ 1 Introduction 
+ 2 Background 
+ 3 Threat model 
+ 4 Methodology  
	+ 4.1 Standard approach 
	+ 4.2 Probability-based approach 
	+ 4.3 Language-Model based approach 

+ 5 Dataset  
	+ 5.1 Description 
	+ 5.2 Datasets Analyses 

+ 6 Evaluation  
	+ 6.1 Experimental Settings 
	+ 6.2 Results 
	+ 6.3 Discussion 

+ 7 Related Work 
+ 8 Conclusions 
+ 9 Acknowledgment 
+ References 
+ A Dataset Analyses  
	+ A.1 Wordlists Coverage Ratio Analysis 
	+ A.2 Stemming Analysis 
	+ A.3 Similarity Analysis



