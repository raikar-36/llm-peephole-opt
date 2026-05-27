define i64 @pattern_xor_255_64(i64 %x) {
entry:
  %result = xor i64 %x, 255
  ret i64 %result
}
