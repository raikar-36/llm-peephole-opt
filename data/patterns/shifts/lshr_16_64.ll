define i64 @pattern_lshr_16_64(i64 %x) {
entry:
  %result = lshr i64 %x, 16
  ret i64 %result
}
