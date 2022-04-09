import seaborn as sns


palette = dict(zip(list('ABCDEFG'), [tuple(int(c*255) for c in cs) for cs in sns.color_palette("husl", 7)]))

print(palette)