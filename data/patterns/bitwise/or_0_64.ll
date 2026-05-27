define i64 @pattern_or_0_64(i64 %x) {
entry:
  %result = or i64 %x, 0
  ret i64 %result
}
