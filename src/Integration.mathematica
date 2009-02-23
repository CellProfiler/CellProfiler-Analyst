Integrate[PDF[BetaDistribution[c,d],x]*CDF[BetaDistribution[a,b],x],{x,0,1},Assumptions->{a>0,b>0,c>0,d>0}]


In[1]:= Integrate[PDF[BetaDistribution[c,d],x]*CDF[BetaDistribution[a,b],x],{x,0,1},Assumptions->{a>0,b>0,c>0,d>0}]

Out[1]= (Gamma[a] Gamma[a + c] Gamma[d] 
 
>      HypergeometricPFQRegularized[{a, 1 - b, a + c}, {1 + a, a + c + d}, 1])
 
>      / (Beta[a, b] Beta[c, d])

http://functions.wolfram.com/HypergeometricFunctions/HypergeometricPFQRegularized/02/0001/MainEq1.gif


Integrate[PDF[BetaDistribution[111.52056534719972, 0.31516669716616263],x]*CDF[BetaDistribution[90.520565347199721, 0.31516669716616263],x],{x,0,1}]


Integrate[PDF[BetaDistribution[a+c,b+d],x]*CDF[BetaDistribution[a,b],x],{x,0,1},Assumptions->{a>0,b>0,c>=0,d>=0,(c+d)>0,c in Integers, d in Integers}]
