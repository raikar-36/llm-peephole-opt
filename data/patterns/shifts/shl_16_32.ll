define i32 @pattern_shl_16_32(i32 %x) {
entry:
  %result = shl i32 %x, 16
  ret i32 %result
}
