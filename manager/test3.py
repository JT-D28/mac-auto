d=[{
    'b':1,
    'a':2
},
{
    'b':4,
    'a':1
    }
]
d.sort(key=lambda e:e.get('a'))
print(d)