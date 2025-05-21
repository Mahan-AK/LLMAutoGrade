## Exercise 1.1 (Computer scientist's random variables). (Total: 8 points)

Consider the following algorithm:
1. Throw a coin $C \xleftarrow{\text{unif}} \{0,1\}$.
2. Choose $X \xleftarrow{\text{unif}} [0, 1]$ uniformly.
3. Roll a die $D \xleftarrow{\text{unif}} \{1,2,3,4,5,6\}$.
4. If $C=0$ then
5. Let $Z \leftarrow D + X$.
6. Else
7. Let $Z \leftarrow D - X$.
8. Return $Z$

The output $Z$ of this algorithm is a random variable.

(i) Compute its expection $E(Z)$. [3 points]
**Solution.**
Notice
* $E(X) = \int_0^1 x \, dx = 1/2$,
* $E(X^2) = \int_0^1 x^2 \, dx = 1/3$ and
* $E(D) = \sum_{d \in \{1,2,3,4,5,6\}} d \text{ prob}(D = d) = 21/6 = 7/2$,
* $E(D^2) = \sum_{d \in \{1,2,3,4,5,6\}} d^2 \text{ prob}(D = d) = (1^2+2^2+3^2+4^2+5^2+6^2)/6 = 91/6$.

Thus conditioned on $C = 0$ we find
$$E[Z | C = 0] = E(D + X) = E(D) + E(X) = 4$$

and conditioned on $C = 1$ we find
$$E[Z | C = 1] = E(D - X) = E(D) - E(X) = 3.$$

Interludium total probability: We can always split probalities into pieces via conditional probabilities on the pieces of a partition of the universe:
If $\Omega = \bigcup_i \Omega_i$ then
$$\text{prob}(V \in A) = \sum_i \text{ prob}(V \in A | \Omega_i) \text{ prob}(\Omega_i)$$
This translates to expected values:
$$E(V) = \sum_i E(V | \Omega_i) \text{ prob}(\Omega_i).$$
You can easily check this by using the definitions. This is the tool to deal with case distinctions in programs in general.

In the case at hand the interludium means that we simply compute
$$E(Z) = \frac{1}{2} E[Z|C = 0]+\frac{1}{2} E[Z|C = 1].$$
and so
$$E(Z) = E(D) = 7/2$$

(ii) Compute its second moment $E(Z^2)$. [4 points]
**Solution.**
Similarly we get
$$E(Z^2) = E((D + X)^2) \text{ prob}(C = 0) + E((D - X)^2) \text{ prob}(C = 1)$$
$$= \frac{1}{2} (E(D^2) + 2 E(D) E(X) + E(X^2))$$
$$+ \frac{1}{2} (E(D^2) - 2 E(D) E(X) + E(X^2))$$
$$= E(D^2) + E(X^2) = 91/6 + 1/3 = 31/2$$

(iii) Compute its variance $\text{var}(Z)$. [1 point]
**Solution.**
Consequently, $\text{var}(Z) = E(Z^2) - E(Z)^2 = 31/2 - (7/2)^2 = 13/4$.

## Exercise 1.2 (Apply Markov's and Chebyshev's inequalities). (Total: 12 points)

In this exercise you shall test the quality of Markov's and Chebyshev's inequalities.

(i) Consider a uniform real number from the unit interval, ie. $U \xleftarrow{\text{unif}} [0, 1]$ uniformly chosen.
a) Plot $\text{prob}(U \ge a)$ and $E[U]/a$ as functions of $a$. [1 point]
**Solution.**
The solution consists of the plot. In the original PDF, this plot shows $\text{prob}(U \ge a)$ (actual probability, $1-a$ for $a \in [0,1]$, then 0) as a blue line and the Markov bound $E[U]/a = 1/(2a)$ as a red line, for $a \in [0, 2]$.

b) Plot $\text{prob}(|U - E[U]| \ge c)$ and $\text{var }U/c^2$ as functions of $c$. [1 point]
**Solution.**
The solution consists of the plot. In the original PDF, this plot shows $\text{prob}(|U - E[U]| \ge c)$ (actual probability, $E[U]=1/2$, this is $1-2c$ for $c \in [0,1/2]$, then 0) as a blue line and the Chebyshev bound $\text{var }U/c^2 = (1/12)/c^2$ as a red line, for $c \in [0, 1]$.

c) Compare and interpret. [2 points]
**Solution.**
We can see that the Markov bound for the variable $U$ is very loose and does not contain much information. For example, in the interval $(0, 1/2]$ the values of $E[U]/a$ are larger than 1, even if we know that all probabilities are naturally bounded by 1. The tail bound is also extremely loose, as even if $U > 1$ is impossible, we still see a significant value of the Markov bound there.

The Chebyshev inequality is also quite meaningless for small values of $c$. Even for $c$ close to 0.5, which is the end of the range that $c$ can take, we still have a lot of difference between the bound and the actual function. The tail bounds here are much better than in the Markov case and tend to 0 very quickly.

(ii) Consider a normally distributed real number with mean 0 and variance 1, ie. $X \sim \mathcal{N}(0, 1)$.
a) Plot $\text{prob}(X \ge a)$ and $E[|X|]/a$ as functions of $a$. [1 point]
**Solution.**
The solution consists of the plot. In the original PDF, this plot shows $\text{prob}(X \ge a)$ (actual probability, tail of $\mathcal{N}(0,1)$) as a blue line and the bound $E[|X|]/a = \sqrt{2/\pi}/a$ as a red line, for $a \in [0, 4]$.

b) Plot $\text{prob}(|X - E[X]| \ge c)$ and $\text{var }X/c^2$ as functions of $c$. [1 point]
**Solution.**
The solution consists of the plot. In the original PDF, this plot shows $\text{prob}(|X - E[X]| \ge c)$ (actual probability, $E[X]=0$, so $2\Phi(-c)$ for $c>0$) as a blue line and the Chebyshev bound $\text{var }X/c^2 = 1/c^2$ as a red line, for $c \in [0, 4]$.

c) Compare and interpret. [2 points]
**Solution.**
The most important thing to note is that Markov's inequality does not apply here. This is due to the fact, that X is a random variable that can take negative values. Markov is only applicable for non-negative random variables.
Chebyshev's inequality yields a decent bound, except for very small $c$.

(iii) Consider a fair die, ie. $D \xleftarrow{\text{unif}} \{1, 2, 3, 4, 5, 6\}$ with uniform distribution.
a) Plot $\text{prob}(D \ge a)$ and $E[D]/a$ as functions of $a$. [1 point]
**Solution.**
The solution consists of the plot. In the original PDF, this plot shows $\text{prob}(D \ge a)$ (actual probability, a step function) as a blue line and the Markov bound $E[D]/a = (7/2)/a$ as a red line, for $a \in [0, 7]$.

b) Plot $\text{prob}(|D - E[D]| \ge c)$ and $\text{var }D/c^2$ as functions of $c$. [1 point]
**Solution.**
The solution consists of the plot. In the original PDF, this plot shows $\text{prob}(|D - E[D]| \ge c)$ (actual probability, $E[D]=7/2$, a step function) as a blue line and the Chebyshev bound $\text{var }D/c^2 = (35/12)/c^2$ as a red line, for $c \in [0, 3]$.

c) Compare and interpret. [2 points]
**Solution.**
We see again that the Markov inequality is a quite rough bound. The tail bound of Chebychev is better, but it's still not very good.

## Exercise 1.3 (When is Markov sharp?). (Total: 4 points)

(i) Show that for any $a > 0$ there exists a probability distribution such that the Markov inequality is sharp, ie. $\text{prob}(X \ge a) = E(X)/a$. Use the prob (...) notation to write down the distribution explicitly. [4 points]
Hint: Recall the proof from the lecture. If it helps you, restrict to the discrete setting.
**Solution.**
We use that $\text{prob}(X \in I) = E(\mathbb{I}_{\{X \in I\}})$ since
$$E(\mathbb{I}_{\{X \in I\}}) = \sum_{i=0}^1 i \cdot \text{ prob}(\mathbb{I}_{\{X \in I\}} = i)$$
$$= 1 \cdot \text{ prob}(\mathbb{I}_{\{X \in I\}} = 1)$$
$$= \text{ prob}(X \in I) .$$

Applied to the equation, we find that the following are equivalent:
$$\text{prob}(X \ge a) = E(X)/a$$
$$a \cdot \text{ prob}(X \ge a) = E(X)$$
$$E(a \cdot \mathbb{I}_{\{X \ge a\}}) = E(X \cdot \mathbb{I}_{\{X \ge 0\}}).$$
$$E(X \cdot \mathbb{I}_{\{X \ge 0\}} - a \cdot \mathbb{I}_{\{X \ge a\}}) = 0.$$
$$E(X \cdot \mathbb{I}_{\{0 \le X < a\}} + (X - a) \cdot \mathbb{I}_{\{X \ge a\}}) = 0.$$
Since $X \cdot \mathbb{I}_{\{0 \le X < a\}} \ge 0$ and $(X-a) \cdot \mathbb{I}_{\{X \ge a\}} \ge 0$, their sum has expectation zero if and only if both terms are zero almost surely. Thus,
$$E(X \cdot \mathbb{I}_{\{0 \le X < a\}}) = 0 \quad \text{and} \quad E((X - a) \cdot \mathbb{I}_{\{X \ge a\}}) = 0.$$
This implies (since $X \ge 0$ and $a>0$):
$$\text{prob}(0 < X < a) = 0 \quad \text{and} \quad \text{prob}(X > a) = 0.$$
For the last step we use: for any set $M$ and any random variable $Z$ with $Z \ge 0$ on $M$ we have that $E(Z \cdot \mathbb{I}_M) = 0$ implies $\text{prob}(Z \in M \setminus \{0\}) = 0$. As a consequence Markov is sharp iff $\text{prob}(X \in \{0, a\}) = 1$.

In other words, each distribution that satisfies above requirement is given by some $p \in [0, 1]$ and
$$\text{prob}(X = a) = p, \text{ prob}(X = 0) = 1 - p.$$
(To match $E(X)/a = p$, we need $ap/a = p$, which holds. And $\text{prob}(X \ge a)=p$. So this is sharp.)