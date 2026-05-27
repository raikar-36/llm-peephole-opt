define i32 @pattern_shl_31_32(i32 %x) {
entry:
  %result = shl i32 %x, 31
  ret i32 %result
}
