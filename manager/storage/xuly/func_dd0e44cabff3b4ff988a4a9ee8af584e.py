def getId_no():
    str1_6=["110101","150422","120101","130101","330101","440101","440113","441201",
            "340101","340201","450101","150101","150401","150423","150602","150801",
            "152501","152921"]
    str7_9=["195","196","197","198"]
    coefficientArray = [ "7","9","10","5","8","4","2","1","6","3","7","9","10","5","8","4","2"]# 加权因子
    MapArray=["1","0","X","9","8","7","6","5","4","3","2"]
    str10=str(random.randint(1, 9))
    str11_12 = str(random.randint(1, 12)).zfill(2)
    str13_14 = str(random.randint(1, 27)).zfill(2)
    str15_17 = str(random.randint(1, 999)).zfill(3)
    m = random.randint(0, len(str1_6)-1)
    n = random.randint(0, len(str7_9)-1)
    tempStr=str1_6[m]+str7_9[n]+str10+str11_12+str13_14+str15_17
    total = 0
    for i in range(len(tempStr)):
        total = total + int(tempStr[i])*int(coefficientArray[i])
    parityBit=MapArray[total%11]
    ResultIDCard=tempStr+parityBit
    return ResultIDCard
