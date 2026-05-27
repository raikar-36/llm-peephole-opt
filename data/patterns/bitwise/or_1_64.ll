define i64 @pattern_or_1_64(i64 %x) {
entry:
  %result = or i64 %x, 1
  ret i64 %result
}
