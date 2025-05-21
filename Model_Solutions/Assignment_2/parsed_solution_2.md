Foundations of data science
AMIT RANA, BASTIAN SCHNEIDER, GERD MUND, PENELOPE MÜCK,
JONATHAN LENNARTZ, ANNIKA TARNOWSKI & MICHAEL NÜSKEN

2. Exercise sheet
Handin as announced on eCampus

## Exercise 2.1 (Prove a Chernoff bound). fits to 03 (Total: 10 points)

In several steps you shall prove the

Theorem (Chernoff, positive part). Let $X = \sum_{i=1}^n X_i$ with independent,
$p$-biased Bernoulli variables $X_i \in \{0,1\}$ with prob $(X_i = 1) = p$.
Let $\varepsilon \in ]0, \frac{1}{2}[$. Then for some constant $c > 0$ we have
$$
\text{prob} (X - EX > \varepsilon EX) < e^{-c\varepsilon^2 EX}
$$

(i) Compute EX. [1 point]
**Solution.**
By the linearity of the expected value, we have that
$$
E(X) = E\left(\sum_{i=1}^n X_i\right) = \sum_{i=1}^n E(X_i).
$$
A simple computation shows that $E(X_i) = p$, such that
$$
E(X) = \sum_{i=1}^n p = np.
$$

(ii) For $\alpha > 0$ compute $E e^{\alpha X}$. [Do not forget to reason!] [3 points]
**Solution.**
At first, one can compute
$$
e^{\alpha X} = e^{\alpha\sum_{i=1}^n X_i} = \prod_{i=1}^n e^{\alpha X_i}.
$$
Now as the $X_i$ are independent, so are the variables $e^{\alpha X_i}$. Hence
$$
E(e^{\alpha X}) = E\left(\prod_{i=1}^n e^{\alpha X_i}\right) = \prod_{i=1}^n E(e^{\alpha X_i}).
$$

It remains to compute
$$
E (e^{\alpha X_i}) = \text{prob} (X_i = 1) \cdot e^{\alpha\cdot 1} + \text{prob} (X_i = 0) \cdot e^{\alpha\cdot 0}
= p \cdot e^{\alpha} + (1 - p) \cdot 1 = 1 + p(e^{\alpha} - 1),
$$
so that overall we obtain
$$
E (e^{\alpha X}) = \prod_{i=1}^n (1 + p(e^{\alpha} - 1)) = (1 + p(e^{\alpha} - 1))^n
$$

(iii) Use $1 + x \le e^x$ to estimate $E e^{\alpha X}$ by $e^{\beta np}$ for some $\beta$. [1 point]
**Solution.**
If we use $x = p(e^{\alpha} - 1)$ and apply the inequality, we obtain
$$
1 + p(e^{\alpha} - 1) \le e^{p(e^{\alpha}-1)}.
$$
Hence
$$
E(e^{\alpha X}) = (1 + p(e^{\alpha} - 1))^n \le (e^{p(e^{\alpha}-1)})^n = e^{np(e^{\alpha}-1)},
$$
so for $\beta = (e^{\alpha} – 1)$ we obtain the desired result.

(iv) Prove that $e^{\alpha} - 1 - \alpha(1 + \varepsilon) \le -\frac{1}{3}\varepsilon^2$ for a suitable $\alpha$ and for each $\varepsilon \in ]0, \frac{1}{2}[$. [3 points]
**Solution.**
We start by noting, that $e^{\alpha} - 1 - \alpha(1 + \varepsilon) \le -\frac{1}{3}\varepsilon^2$ is equivalent to
$$
e^{\alpha} - 1 - \alpha(1 + \varepsilon) + \frac{1}{3}\varepsilon^2 \le 0.
$$
If we consider the left hand side as a function of $\alpha$, we can compute that the minimum is obtained at $\alpha = \ln(1 + \varepsilon)$. Because of this we will consider $\alpha = \ln(1 + \varepsilon)$ and it remains to show that for any $\varepsilon$ in question
$$
f(\varepsilon) = e^{\ln(1+\varepsilon)} - 1 - \ln(1 + \varepsilon)(1 + \varepsilon) + \frac{1}{3}\varepsilon^2 = \varepsilon - \ln(1 + \varepsilon)(1 + \varepsilon) + \frac{1}{3}\varepsilon^2 \le 0.
$$
We can compute that $f(0) = 0$, so our aim will be to show, that $f'(\varepsilon) \le 0$ for $\varepsilon \in ]0, \frac{1}{2} [$ such that the function $f(\varepsilon)$ will decrease (or stay constant) and hence be 0 or negative in the given interval.
Computing $f'$ yields
$$
f'(\varepsilon) = 1 - \frac{1}{1+\varepsilon}(1+\varepsilon) - \ln(1 + \varepsilon) + \frac{2}{3}\varepsilon = \frac{2}{3}\varepsilon - \ln(1 + \varepsilon).
$$
Again we have $f'(0) = 0$ and it's not immediate to see that $f'(\varepsilon) \le 0$. But if we compute the second derivative, we have
$$
f''(\varepsilon) = \frac{2}{3} - \frac{1}{1+\varepsilon},
$$
which is negative for $\varepsilon \in ]0, \frac{1}{2}[$. So in this interval, $f'(\varepsilon)$ will be a decreasing function, and as it starts at 0, it will be negative. So also $f$ will be a decreasing function and as it starts at 0 as well, it will be negative throughout $\varepsilon \in ]0, \frac{1}{2}[$.
So indeed, the given inequality holds for $\alpha = \ln(1 + \varepsilon)$ and $\varepsilon \in ]0, \frac{1}{2}[$.

For confirmation:
The graph provided in the document (PDF, page 15) illustrates the functions $f(\varepsilon)$ and $f'(\varepsilon)$ discussed in the proof for $\varepsilon \in [0, 1.5]$: $f(\varepsilon) = \varepsilon - \ln(1 + \varepsilon)(1 + \varepsilon) + \frac{1}{3}\varepsilon^2$ (blue curve, mostly negative or zero in the relevant range) and $f'(\varepsilon) = \frac{2}{3}\varepsilon - \ln(1 + \varepsilon)$ (pink curve). This visually supports that $f(\varepsilon) \le 0$ for $\varepsilon \in ]0, 1/2[$.

(v) Apply Markov's inequality for $Z = e^{\alpha X}$ to prove the theorem. [2 points]
**Solution.**
What we want to prove is that
$$
\text{prob} (X - EX > \varepsilon EX) < e^{-c\varepsilon^2 EX}.
$$
To transform the probability into a form such that we can apply Markov, we calculate
$$
\text{prob} (X - EX > \varepsilon E X) = \text{prob} (X > (1 + \varepsilon) E X) = \text{prob} (e^{\alpha X} > e^{\alpha(1+\varepsilon) EX}),
$$
where the last equality holds as $\alpha > 0$ (since $\alpha = \ln(1+\varepsilon)$ and $\varepsilon \in ]0, 1/2[$), such that $e^{\alpha x}$ is a monotone increasing function in $x$.
But $Z = e^{\alpha X}$ is now a positively distributed random variable, such that we can apply Markov's inequality:
$$
\text{prob} (e^{\alpha X} > e^{\alpha(1+\varepsilon) EX}) = \text{prob} (Z > e^{\alpha(1+\varepsilon) EX}) \le \frac{E(Z)}{e^{\alpha(1+\varepsilon) EX}}.
$$
But we have already estimated $E(Z)$ and inserting this leads to
$$
\frac{E(Z)}{e^{\alpha(1+\varepsilon) EX}} \le \frac{e^{np(e^{\alpha}-1)}}{e^{\alpha(1+\varepsilon) np}} = e^{np((e^{\alpha}-1)-(\alpha(1+\varepsilon))) }.
$$
Now we can use our inequality from the previous part and the fact that $t \mapsto e^{t EX}$ is a positive monotone increasing function in $t$, to conclude that
$$
e^{np((e^{\alpha}-1)-(\alpha(1+\varepsilon)))} \le e^{np(-\frac{1}{3}\varepsilon^2)} = e^{-\frac{1}{3}\varepsilon^2 EX} = e^{-c\varepsilon^2 EX},
$$
for $c = \frac{1}{3}$.

You may want to consider the negative part, namely that also
$$
\text{prob} (X - EX \le -\varepsilon EX) < e^{-c\varepsilon^2 EX}.
$$
Hint: $\alpha < 0$ does help.
+0

## Exercise 2.2 (Annuli). fits to 03 (Total: 8 points)

(i) Compute and estimate the volume of the $\frac{1}{100}$-annulus compared to the volume of the $d$-dimensional ball $B^d$. [1 point]
**Solution.**
By the formula from the lecture we know that the volume of the annulus of width $\varepsilon$ of the $d$-dimensional ball, here denoted $A^d_{\varepsilon}$, is
$$
\text{vol} (A^d_{\varepsilon}) = \text{vol}(B^d) – (1 - \varepsilon)^d \text{vol}(B^d).
$$
So for $\varepsilon = \frac{1}{100}$ we obtain
$$
\text{vol} (A^d_{\frac{1}{100}}) = \text{vol}(B^d) - \left(1 - \frac{1}{100}\right)^d \text{vol}(B^d),
$$
so compared to the $d$-dimensional ball we have
$$
\frac{\text{vol}(A^d_{\frac{1}{100}})}{\text{vol}(B^d)} = 1 - \left(1 - \frac{1}{100}\right)^d \ge 1 - e^{-\frac{1}{100}d}.
$$
So especially we have
$$
\frac{\text{vol}(A^d_{\frac{1}{100}})}{\text{vol}(B^d)} \xrightarrow{d \to \infty} 1.
$$

(ii) Compute and estimate the volume of the $\frac{1}{\sqrt{d}}$-annulus compared to the volume of the $d$-dimensional ball $B^d$. [2 points]
**Solution.**
With the same formula as above, for $\varepsilon = \frac{1}{\sqrt{d}}$ we obtain
$$
\text{vol} (A^d_{\frac{1}{\sqrt{d}}}) = \text{vol}(B^d) - \left(1 - \frac{1}{\sqrt{d}}\right)^d \text{vol}(B^d),
$$
so compared to the $d$-dimensional ball we have
$$
\frac{\text{vol}(A^d_{\frac{1}{\sqrt{d}}})}{\text{vol}(B^d)} = 1 - \left(1 - \frac{1}{\sqrt{d}}\right)^d \ge 1 - e^{-\frac{1}{\sqrt{d}}d} = 1 - e^{-\sqrt{d}}.
$$
So especially, we have
$$
\frac{\text{vol}(A^d_{\frac{1}{\sqrt{d}}})}{\text{vol}(B^d)} \xrightarrow{d \to \infty} 1.
$$

(iii) Compute and estimate the volume of the $\frac{1}{d^2}$-annulus compared to the volume of the $d$-dimensional ball $B^d$. [1 point]
**Solution.**
With the same formula as above, for $\varepsilon = \frac{1}{d^2}$ we obtain
$$
\text{vol} (A^d_{\frac{1}{d^2}}) = \text{vol}(B^d) - \left(1 - \frac{1}{d^2}\right)^d \text{vol}(B^d),
$$
so compared to the $d$-dimensional ball we have
$$
\frac{\text{vol}(A^d_{\frac{1}{d^2}})}{\text{vol}(B^d)} = 1 - \left(1 - \frac{1}{d^2}\right)^d \ge 1 - e^{-\frac{1}{d^2}d} = 1 - e^{-\frac{1}{d}}.
$$
Actually applying an appropriate upper bound we find
$$
\frac{\text{vol}(A^d_{\frac{1}{d^2}})}{\text{vol}(B^d)} \xrightarrow{d \to \infty} 0.
$$

(iv) Plot the three functions and the relative volume of the $\frac{1}{\sqrt{d}}$-annulus for $d = 1..20$. [2 points]
**Solution.**
The plot provided in the document (PDF page 17) displays the relative volumes $V_{rel}(\varepsilon, d) = 1 - (1-\varepsilon)^d$ (solid lines) and their lower bound estimates $1 - e^{-\varepsilon d}$ (dashed lines) for $d=1, \dots, 20$.
The three functions plotted are:
1.  For $\varepsilon = 1/100$ (red lines): $V_{rel}(1/100, d) = 1 - (1-1/100)^d$ and the estimate $1 - e^{-d/100}$.
2.  For $\varepsilon = 1/\sqrt{d}$ (blue lines): $V_{rel}(1/\sqrt{d}, d) = 1 - (1-1/\sqrt{d})^d$ and the estimate $1 - e^{-\sqrt{d}}$.
3.  For $\varepsilon = 1/d^2$ (black lines): $V_{rel}(1/d^2, d) = 1 - (1-1/d^2)^d$ and the estimate $1 - e^{-1/d}$.
The caption from the document notes: "Here, the true functions are drawn as solid lines, the estimates as dashed lines."

(v) For which $\varepsilon$ does the $\varepsilon$-annulus have at least 99% of the ball volume? [2 points]
**Solution.**
If we consider the previous picture, the graph in which we have control of both lower and higher dimensions, is the graph of $\varepsilon = \frac{c}{d}$. The idea now is to consider $\varepsilon = \frac{c}{d}$ to get a different constant. We compute that the volume of the annulus compared to the ball itself is
$$
\left(1 - \left(1 - \frac{c}{d}\right)^d\right) \ge 1 - e^{-c}.
$$
To obtain $1 - e^{-c} > 0.99$, we need to solve $e^{-c} < 0.01$. As the exponential function is monotone increasing, this is equivalent to
$$
-c < \ln(0.01) \Leftrightarrow c > \ln(100).
$$
So especially for $c = \ln(100) \approx 4.6054$ we have that an $\varepsilon = \frac{c}{d}$-annulus contains more than 99% of the volume of any $d$-dimensional ball.

## Exercise 2.3 (Gamma). fits to 04 (Total: 12 points)

(i) Prove that $\Gamma (\frac{1}{2}) = \sqrt{\pi}$. [4 points]
Hint: Change the variable and use $\int_{-\infty}^{\infty} e^{-x^2} dx = \sqrt{\pi}$.
**Solution.**
We are combining a few elementary transformations on integrals to obtain that. It needs one 'standard' substitution and one trick.
$$
\Gamma\left(\frac{1}{2}\right) = \int_0^\infty x^{\frac{1}{2}-1} e^{-x} dx = \int_0^\infty x^{-\frac{1}{2}} e^{-x} dx.
$$
Use the substitution $x=y^2$, $dx=2y dy$.
$$
\int_0^\infty x^{-\frac{1}{2}} e^{-x} dx = \int_0^\infty (y^2)^{-\frac{1}{2}} e^{-y^2} 2y dy = \int_0^\infty y^{-1} e^{-y^2} 2y dy = \int_0^\infty 2 e^{-y^2} dy.
$$
Since $e^{-y^2}$ is an even function, $\int_{-\infty}^\infty e^{-y^2} dy = 2 \int_0^\infty e^{-y^2} dy$.
Using the hint, $\int_{-\infty}^\infty e^{-y^2} dy = \sqrt{\pi}$, so $\int_0^\infty e^{-y^2} dy = \frac{\sqrt{\pi}}{2}$.
$$
\int_0^\infty 2 e^{-y^2} dy = 2 \cdot \frac{\sqrt{\pi}}{2} = \sqrt{\pi}.
$$

(ii) Prove that $\int_{-\infty}^\infty e^{-x^2} dx = \sqrt{\pi}$. [4 points]
Hint: To that end consider $\int_{\mathbb{R}^2} e^{-(y^2+z^2)} dy dz$. Use the substitution $y = r \cos(\phi), z = r \sin(\phi)$ to express this with polar coordinates.
**Solution.**
For computing this integral the simplest way I know is to square it:
$$
\left(\int_{-\infty}^\infty e^{-x^2} dx\right)^2 = \left(\int_{-\infty}^\infty e^{-y^2} dy\right) \left(\int_{-\infty}^\infty e^{-z^2} dz\right) = \int_{-\infty}^\infty \int_{-\infty}^\infty e^{-y^2} e^{-z^2} dy dz = \int_{\mathbb{R}^2} e^{-(y^2+z^2)} dy dz.
$$
Use the substitution $(y,z)=(r \cos\phi, r \sin\phi)$, $dy dz=r dr d\phi$.
$$
\int_{\mathbb{R}^2} e^{-(y^2+z^2)} dy dz = \int_0^{2\pi} \int_0^\infty e^{-r^2} r dr d\phi.
$$
The inner integral is $\int_0^\infty e^{-r^2} r dr$. Substitute $u=r^2$, $du=2r dr$.
$$
\int_0^\infty e^{-r^2} r dr = \int_0^\infty e^{-u} \frac{1}{2} du = \frac{1}{2} [-e^{-u}]_0^\infty = \frac{1}{2}(0 - (-1)) = \frac{1}{2}.
$$
The outer integral is $\int_0^{2\pi} \frac{1}{2} d\phi = \frac{1}{2} [\phi]_0^{2\pi} = \frac{1}{2} (2\pi) = \pi$.
So, $\left(\int_{-\infty}^\infty e^{-x^2} dx\right)^2 = \pi$.
and thus $\int_{-\infty}^\infty e^{-x^2} dx = \sqrt{\pi}$ (since $e^{-x^2}$ is positive, its integral must be positive).

(iii) Recall the formula for integration by parts (look it up if need be...), $\int_a^b f(x)g'(x) dx = ...$, where $f$ and $g$ are any suitably nice functions. Use this formula to show that indeed $\Gamma(z + 1) = z\Gamma(z)$. [4 points]
**Solution.**
We split the integrand into the parts $x^z$ with derivate $zx^{z-1}$ and $e^{-x}$ with anti-derivative $-e^{-x}$:
$$
\Gamma(z + 1) = \int_0^\infty x^{(z+1)-1} e^{-x} dx = \int_0^\infty x^z e^{-x} dx.
$$
Let $f(x) = x^z$ and $g'(x) = e^{-x}$, so $f'(x) = zx^{z-1}$ and $g(x) = -e^{-x}$.
Using integration by parts $\int_0^\infty f(x)g'(x)dx = [f(x)g(x)]_0^\infty - \int_0^\infty f'(x)g(x)dx$:
$$
\int_0^\infty x^z e^{-x} dx = [-x^z e^{-x}]_0^\infty - \int_0^\infty z x^{z-1} (-e^{-x}) dx.
$$
For $z > 0$, the boundary term is
$$
[-x^z e^{-x}]_0^\infty = \lim_{x \to \infty} (-x^z e^{-x}) - \lim_{x \to 0^+} (-x^z e^{-x}) = 0 - 0 = 0.
$$
The integral becomes
$$
0 - \int_0^\infty z x^{z-1} (-e^{-x}) dx = z \int_0^\infty x^{z-1} e^{-x} dx = z\Gamma(z).
$$
So $\Gamma(z + 1) = z\Gamma(z)$ for $z > 0$.

## Exercise 2.4 (Simplices). fits to 04 (Total: 4 points)

(i) Consider an $n$-simplex
$$
\Delta_n
= \left\{ x \in \mathbb{R}^n \left| \exists x_i \in \mathbb{R}_{\ge 0} : x = \sum_{0 \le i < n} x_i e_i, \sum_{0 \le i < n} x_i \le 1 \right. \right\}
$$
Estimate its near surface volume $\Delta_n \setminus (c + (1 - \varepsilon)(\Delta_n - c))$ with $c$ centroid$(e_0, ..., e_{n-1}, 0)$ relative to its volume. [4 points]
**Solution.**
From the lecture we know that for $A \subset \mathbb{R}^d$, $\varepsilon \in [0, 1]$ if $A_c = c + \lambda(A-c)$ is a scaled version of $A$ with respect to its centroid $c$ by a factor $\lambda$, then $\text{vol}(A_c) = \lambda^d \text{vol}(A)$. Here $d=n$ and $\lambda = 1-\varepsilon$.
The set $A' = c + (1-\varepsilon)(\Delta_n - c)$ is such a scaled version of $\Delta_n$.
Thus, $\text{vol}(c + (1-\varepsilon)(\Delta_n - c)) = (1-\varepsilon)^n \text{vol}(\Delta_n)$.
The near surface volume is $\text{vol}(\Delta_n \setminus (c + (1 - \varepsilon)(\Delta_n - c)))$.
Assuming $c + (1 - \varepsilon)(\Delta_n - c) \subset \Delta_n$, which is true for a convex set and its centroid,
$$
\text{vol}(\Delta_n \setminus (c + (1 - \varepsilon)(\Delta_n - c))) = \text{vol}(\Delta_n) - \text{vol}(c + (1 - \varepsilon)(\Delta_n - c)).
$$
To simplify, we can shift the coordinate system such that the centroid $c$ of the simplex is the origin. In this shifted coordinate system $c = 0$ and we have $(c+(1-\varepsilon)(\Delta_n-c)) = (1-\varepsilon)\Delta_n$. It is given that $(1 - \varepsilon)\Delta_n \subset \Delta_n$ for such a centered set.
The relative volume is then:
$$
\frac{\text{vol}(\Delta_n \setminus (c + (1 - \varepsilon)(\Delta_n - c)))}{\text{vol}(\Delta_n)}
= \frac{\text{vol}(\Delta_n) - \text{vol}((1 - \varepsilon)\Delta_n)}{\text{vol}(\Delta_n)}
$$
Using $\text{vol}((1 - \varepsilon)\Delta_n) = (1 - \varepsilon)^n \text{vol}(\Delta_n)$, we get:
$$
= 1 - \frac{(1 - \varepsilon)^n \text{vol}(\Delta_n)}{\text{vol}(\Delta_n)}
= 1 - (1 - \varepsilon)^n
$$
Using the inequality $1-x \le e^{-x}$ for $x=\varepsilon$, so $(1-\varepsilon) \le e^{-\varepsilon}$. Therefore, $(1-\varepsilon)^n \le (e^{-\varepsilon})^n = e^{-\varepsilon n}$.
This means $-(1-\varepsilon)^n \ge -e^{-\varepsilon n}$.
So, $1 - (1 - \varepsilon)^n \ge 1 - e^{-\varepsilon n}$.
Thus, the relative volume is $1 - (1 - \varepsilon)^n \ge 1 - e^{-\varepsilon n}$.