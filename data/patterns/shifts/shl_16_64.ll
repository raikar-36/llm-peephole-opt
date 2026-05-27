define i64 @pattern_shl_16_64(i64 %x) {
entry:
  %result = shl i64 %x, 16
  ret i64 %result
}
