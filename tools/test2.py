import re
d1='''"srcNoteCode":"{{srcNoteCode}}",       "orgCode":"{{orgCode}}",'''

d2='''"srcNoteCode":"{{srcNoteCode}}",       "srcNoteCode2":"{{srcNoteCode2}}",       "orgCode":"{{orgCode}}",'''

d3='''"srcNoteCode":"{{srcNoteCode}}",
      "orgCode":"{{orgCode}}",'''

o='''{
  "transCode":"{{transCode_single}}",
  "transType":"{{transType_single}}",
  "version":"{{version}}",
  "reqSeq":"{{reqSeq}}",
  "transDate":"{{transDate}}",
  "transTime":"{{transTime}}",
  "charset":"{{charset}}",
  "merchantNum":"{{merchantNum}}",
  "systemCode":"{{systemCode}}",
  "remark":"{{remark_Sass}}",
  "reserve":"{{reserve}}",
  "body":
    {
      "srcNoteCode":"{{srcNoteCode}}",
      "orgCode":"{{orgCode}}",
      "deptCode":"{{deptCode}}",
      "payDate":"{{payDate}}",
      "payTypeCode":"{{payTypeCode_single}}",
      "settlementMode":"{{settlementMode_singlePay}}",
      "capitalCategoryCode":"{{capitalCategoryCode}}",
      "budgetItemCode":"{{budgetItemCode}}",
      "abstracts":"{{abstracts}}",
      "isurgent":"{{isurgent}}",
      "purpose":"{{purpose}}",
      "memo":"{{memo}}",
      "payerAcctNo":"{{payerAcctNo}}",
      "currencyCategory":"{{currencyCategory}}",
      "transAmount":"{{transAmount}}",
      "payeeBankNo":"{{payeeBankNo}}",
      "payeeAcctNo":"{{payeeAcctNo}}",
      "payeeName":"{{payeeName}}",
      "payeePrivateFlag":"{{payeePrivateFlag}}",
      "payeeEmailAddr":"{{payeeEmailAddr}}",
      "payeeCardType":"{{payeeCardType}}",
      "interbakLineNo":"{{interbakLineNo}}"
    }
}'''
# o=re.sub(d2, d1,o)
print(d1.encode())
print(d3.encode())