define i64 @pattern_shl_3_64(i64 %x) {
entry:
  %result = shl i64 %x, 3
  ret i64 %result
}
