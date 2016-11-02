import matplotlib.pyplot as plt
import os
import pandas as pd

os.chdir('ffdata')

overall_df = pd.read_csv('overall.csv', index_col=0)

fig = plt.figure()
ax = fig.add_subplot(111)

names = overall_df['owner name'].tolist()
x = overall_df['avg points'].tolist()
y = overall_df['avg against'].tolist()
name_dict = {x[n]:names[n] for n in range(len(names))}
plt.scatter(x,y)

#get and set axes limits
xmin, xmax = plt.xlim()
ymin, ymax = plt.ylim()
ax.set_xlim((xmin,xmax))
ax.set_ylim((ymin,ymax))

plt.plot([xmin-5, xmax+5],[(ymin+ymax)/2, (ymin+ymax)/2])
plt.plot([(xmin+xmax)/2, (xmin+xmax)/2], [ymin-5, ymax+5])

for group in zip(x,y):
	ax.annotate('{}'.format(name_dict[group[0]]), xy=group, xytext=(group[0]+.3,group[1]+.3))

plt.gca().invert_yaxis()

plt.show()