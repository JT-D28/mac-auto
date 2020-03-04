def get_1_to_6_digit_numbers():
  import random
  final=''
  ws=random.randint(1, 2)
  for x in range(ws):
    r=int(random.random()*10)
    final+=str(r)
  return final