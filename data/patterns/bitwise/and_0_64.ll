define i64 @pattern_and_0_64(i64 %x) {
entry:
  %result = and i64 %x, 0
  ret i64 %result
}
