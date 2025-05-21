Foundations of data science
AMIT RANA, BASTIAN SCHNEIDER, GERD MUND, PENELOPE MÜCK, JONATHAN LENNARTZ, ANNIKA TARNOWSKI & MICHAEL NÜSKEN

0. Exercise sheet
Handin as announced on eCampus

Exercise 0.1 (Recall: Random variables).

(i) Consider the course' example: A player has a fair die D resulting in one of $D := \{ \boxplus, \boxplus, \boxplus, \boxplus, \boxplus, \boxplus \}$ with probability $\frac{1}{6}$ each, i.e. $D \sim \mathcal{U}(\{ \boxplus, \dots, \boxplus \})$, and a fair coin $C \sim \{0,1\}$ uniformly.
Actually, our player is a cheater and the coin merely tells whether he decides to cheat or not. In case the coin comes up heads, say that's encoded 1, he changes the die's outcome to $\boxplus$. Denote the variable describing the faked die by F.

(a) Describe F as a function of C and D.

Solution. We have (if we identify the die's results with the numbers 1 to 6)
$$F = \begin{cases} D & \text{if } C = 0 \\ 6 & \text{else.} \end{cases}$$

(b) Note that the pair (C, F) is again a random variable, namely with outputs in $\{0,1\} \times D$. Write down a 2 $\times$ 6-table with its distribution.

Solution. We obtain for all combinations of $C \in \{0, 1\}$ and $F \in \{1, 2, 3, 4, 5, 6\}$ that the probability of $\text{prob} ((C, F) = (c, f))$ takes the values of:

| $(c, f)$ | $f = 1$ | $2$ | $3$ | $4$ | $5$ | $6$ |
|---|---|---|---|---|---|---|
| $c = 0$ | $\frac{1}{12}$ | $\frac{1}{12}$ | $\frac{1}{12}$ | $\frac{1}{12}$ | $\frac{1}{12}$ | $\frac{1}{12}$ |
| $c = 1$ | $0$ | $0$ | $0$ | $0$ | $0$ | $\frac{1}{12}$ |

(c) Prove that (C, F) is not independent.

Solution. If the variables were independent, it should hold that for all $c \in \{0,1\}$, $f \in \{1, 2, 3, 4, 5, 6\}$ we would have
$$\text{prob} (C = c \wedge F = f) = \text{prob} (C = c) \cdot \text{prob} (F = f) .$$
Now we can choose one of the many counterexamples:
$$\text{prob} (C = 1 \wedge F = 1) = 0 \neq \frac{1}{24} = \text{prob} (C = 1) \cdot \text{prob} (F = 1),$$
or just as well
$$\text{prob} (C = 1 \wedge F = 6) = \frac{1}{12} \neq \frac{7}{24} = \text{prob} (C = 1) \cdot \text{prob} (F = 6) .$$

(ii) Consider a continuous random variable U with outcomes in $[0, 1] \subset \mathbb{R}$ with uniform density, i.e. $U \sim \mathcal{U}([0,1])$ with density $p(x) = 1$ for $x \in [0, 1]$ and $p(x) = 0$ otherwise.
Determine the density of $U^2$, i.e. a function q such that
$$\text{prob} (a < U^2 < b) = \int_{a}^{b} q(x) \,dx .$$

Solution. A nice way to see this is to consider the function $Q(x) = \text{prob} (U^2 < x)$.
As it holds that
$$\int_{a}^{b} q(x) \,dx = Q(b) – Q(a)$$
we know that Q must be the anti derivative of q. We compute
$$Q(x) = \text{prob} (U^2 < x) = \begin{cases} 0 & x \leq 0 \\ \text{prob} (U < \sqrt{x}) = \sqrt{x} & 0 < x \leq 1 \\ \text{prob} (U < \sqrt{x}) = 1 & \text{else.} \end{cases}$$
Now we can compute
$$q(x) = Q'(x) = \begin{cases} 0 & x \leq 0 \\ \frac{1}{2\sqrt{x}} & 0 < x < 1 \\ 0 & \text{else.} \end{cases}$$

Exercise 0.2 (Maximum of two dice).
Take two independent fair dice $D_i \sim D := \{ \boxplus, \boxplus, \boxplus, \boxplus, \boxplus, \boxplus \}$ and consider the larger outcome
$$M := \max(D_0, D_1).$$

(i) Compute $\text{prob} (M \leq a)$ for $a \in \mathbb{N}_{\leq 6}$.

Solution. We have by definition
$$\text{prob} (M \leq a) = \text{prob} (D_0 \leq a \wedge D_1 \leq a),$$
and as the dice are independent
$$\text{prob} (D_0 \leq a \wedge D_1 \leq a) = \text{prob} (D_0 \leq a) \cdot \text{prob} (D_1 \leq a) = \frac{a}{6} \cdot \frac{a}{6} = \frac{a^2}{36}.$$

(ii) Compute $\text{prob} (M = a)$ for $a \in \mathbb{N}_{\leq 6}$.

Solution. As the distribution is discrete (meaning: there are just finitely many outputs for M) we have
$$\text{prob} (M = a) = \text{prob} (M \leq a) – \text{prob} (M \leq (a - 1)),$$
such that we can insert from (i), that
$$\text{prob} (M = a) = \frac{a^2}{36} – \frac{(a - 1)^2}{36} = \frac{a^2 - (a^2 - 2a + 1)}{36} = \frac{2a-1}{36}.$$

(iii) Compute $E(M)$.

Solution. We can now sum up
$$E(M) = 1 \cdot \frac{1}{36} + 2 \cdot \frac{3}{36} + 3 \cdot \frac{5}{36} + 4 \cdot \frac{7}{36} + 5 \cdot \frac{9}{36} + 6 \cdot \frac{11}{36}$$
$$= \frac{1 + 6 + 15 + 28 + 45 + 66}{36} = \frac{161}{36} \approx 4.472\text{↧}$$

(iv) Compute $E(M^2)$ and derive $\text{var}(M)$.

Solution. We can similarly sum up
$$E(M^2) = 1^2 \cdot \frac{1}{36} + 2^2 \cdot \frac{3}{36} + 3^2 \cdot \frac{5}{36} + 4^2 \cdot \frac{7}{36} + 5^2 \cdot \frac{9}{36} + 6^2 \cdot \frac{11}{36}$$
$$E(M^2) = 1 \cdot \frac{1}{36} + 4 \cdot \frac{3}{36} + 9 \cdot \frac{5}{36} + 16 \cdot \frac{7}{36} + 25 \cdot \frac{9}{36} + 36 \cdot \frac{11}{36}$$
$$= \frac{1 + 12 + 45 + 112 + 225 + 396}{36} = \frac{791}{36} \approx 21.972\text{↧}$$
and derive the variance
$$\text{var}(M) = E(M^2) – (E(M))^2 = \frac{764 \cdot 36 – (161)^2}{(36)^2} = \frac{1583}{1296} \approx 1.221\text{↧}$$

Side remark: to indicate how a real number was rounded we append a special symbol. Examples: $\pi = 3.141\text{↧} = 3.142\text{↧} = 3.1416\text{┬} = 3.14159\text{↧}$. The height of the platform shows the size of the left-out part and the direction of the antenna indicates whether actual value is larger or smaller than displayed. We write, say, $e = 2.72\text{┬} = 2.71\text{↧}$ as if the shorthand were exact.