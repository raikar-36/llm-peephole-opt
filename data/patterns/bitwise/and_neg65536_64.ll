define i64 @pattern_and_neg65536_64(i64 %x) {
entry:
  %result = and i64 %x, -65536
  ret i64 %result
}
