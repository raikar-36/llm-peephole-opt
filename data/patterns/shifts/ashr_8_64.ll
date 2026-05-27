define i64 @pattern_ashr_8_64(i64 %x) {
entry:
  %result = ashr i64 %x, 8
  ret i64 %result
}
