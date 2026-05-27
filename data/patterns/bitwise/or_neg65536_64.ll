define i64 @pattern_or_neg65536_64(i64 %x) {
entry:
  %result = or i64 %x, -65536
  ret i64 %result
}
