define i32 @pattern_shl_8_32(i32 %x) {
entry:
  %result = shl i32 %x, 8
  ret i32 %result
}
