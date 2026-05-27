define i64 @pattern_shl_2_64(i64 %x) {
entry:
  %result = shl i64 %x, 2
  ret i64 %result
}
