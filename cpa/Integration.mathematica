FullSimplify[Integrate[PDF[BetaDistribution[s*a,s*b],x]*CDF[BetaDistribution[a,b],x],{x,0,1}], {a>0,b>0,b \[NotElement] Integers, s>1}]


In[1]:= Integrate[PDF[BetaDistribution[c,d],x]*CDF[BetaDistribution[a,b],x],{x,0,1},Assumptions->{a>0,b>0,c>0,d>0}]

Out[1]= (Gamma[a] Gamma[a + c] Gamma[d] 
 
>      HypergeometricPFQRegularized[{a, 1 - b, a + c}, {1 + a, a + c + d}, 1])
 
>      / (Beta[a, b] Beta[c, d])

http://functions.wolfram.com/HypergeometricFunctions/HypergeometricPFQRegularized/02/0001/MainEq1.gif


Integrate[PDF[BetaDistribution[111.52056534719972, 0.31516669716616263],x]*CDF[BetaDistribution[90.520565347199721, 0.31516669716616263],x],{x,0,1}]


Integrate[PDF[BetaDistribution[a+c,b+d],x]*CDF[BetaDistribution[a,b],x],{x,0,1},Assumptions->{a>0,b>0,c>=0,d>=0,(c+d)>0,c in Integers, d in Integers}]


A useful identity:
HypergeometricPFQ[{a, b, c}, {d, a - 1}, 1] == ((Gamma[d] Gamma[d - b
- c])/(Gamma[d - b] Gamma[d - c])) (1 - (b c)/((a - 1) (1 + b + c -
d))) /; Re[d - b - c] > 1


Combined with:
(a_i - 1) F = (a_i - a_j - 1) F(a_i - 1) + a_j F(a_i - 1, a_j + 1)


FullSimplify[Integrate[w^(-1-c) Hypergeometric2F1[a+c,1-d, a+c+b, 1/w], {w,1,Infinity}], {a>0, b>0, c>0, d>0}]
FullSimplify[Integrate[w^(a-1) Hypergeometric2F1[a+c,1-b, a+c+d, w], {w,0,1}], {a>0, b>0, c>0, d>0}]

FullSimplify[Integrate[p^(b+d-1) (1-p)^(c+b-1) AppellF1[b, a+b+c+d-2, 1-a, b+c, 1-p, 1-p^2], {p, 0, 1}], {a>0, b>0, c>0, d>0}]