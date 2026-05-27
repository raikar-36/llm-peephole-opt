define i32 @pattern_shl_4_32(i32 %x) {
entry:
  %result = shl i32 %x, 4
  ret i32 %result
}
