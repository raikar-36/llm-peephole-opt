define i64 @pattern_or_2_64(i64 %x) {
entry:
  %result = or i64 %x, 2
  ret i64 %result
}
