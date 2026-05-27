define i64 @pattern_and_2_64(i64 %x) {
entry:
  %result = and i64 %x, 2
  ret i64 %result
}
