define i64 @pattern_and_neg1_64(i64 %x) {
entry:
  %result = and i64 %x, -1
  ret i64 %result
}
