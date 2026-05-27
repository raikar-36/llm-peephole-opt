define i64 @pattern_shl_1_64(i64 %x) {
entry:
  %result = shl i64 %x, 1
  ret i64 %result
}
