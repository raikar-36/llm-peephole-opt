define i64 @pattern_sub_neg128_64(i64 %x) {
entry:
  %result = sub i64 %x, -128
  ret i64 %result
}
