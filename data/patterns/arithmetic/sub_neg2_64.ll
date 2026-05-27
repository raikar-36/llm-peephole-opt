define i64 @pattern_sub_neg2_64(i64 %x) {
entry:
  %result = sub i64 %x, -2
  ret i64 %result
}
