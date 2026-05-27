define i64 @pattern_shl_15_64(i64 %x) {
entry:
  %result = shl i64 %x, 15
  ret i64 %result
}
