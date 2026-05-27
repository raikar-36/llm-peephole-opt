define i32 @pattern_shl_2_32(i32 %x) {
entry:
  %result = shl i32 %x, 2
  ret i32 %result
}
