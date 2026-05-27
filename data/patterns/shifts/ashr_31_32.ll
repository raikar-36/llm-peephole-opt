define i32 @pattern_ashr_31_32(i32 %x) {
entry:
  %result = ashr i32 %x, 31
  ret i32 %result
}
