define i64 @pattern_and_128_64(i64 %x) {
entry:
  %result = and i64 %x, 128
  ret i64 %result
}
